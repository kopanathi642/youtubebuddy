"""
Ollama Local LLM Provider.

Text generation using locally-hosted Ollama with Llama 3.1 8B.
Replaces OpenAI, Gemini, and HuggingFace text generation clients.

Supports:
  - Chat completions with system prompts
  - Streaming responses
  - JSON-mode structured output
  - Cached health detection and instant structured fallback when Ollama is offline
"""
import json
import logging
import time
from typing import Any, Generator

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
RETRY_BACKOFF = 1

_last_health_check = 0.0
_is_ollama_alive = False


def is_ollama_online() -> bool:
    """Check if Ollama is running, caching status for 10 seconds to avoid blocking threads."""
    global _last_health_check, _is_ollama_alive
    now = time.time()
    if now - _last_health_check < 10.0:
        return _is_ollama_alive

    _last_health_check = now
    try:
        r = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=0.8)
        _is_ollama_alive = (r.status_code == 200)
    except Exception:
        _is_ollama_alive = False

    return _is_ollama_alive


def _build_messages(prompt: str, system: str | None = None) -> list[dict[str, str]]:
    """Build the Ollama chat messages array."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def _generate_offline_fallback(prompt: str, system: str | None = None, json_mode: bool = False) -> str:
    from app.ai.providers.errors import ProviderUnavailable
    raise ProviderUnavailable("Text generation requires a configured, reachable model. No sample text was generated.", "text")

def generate_text(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
    json_mode: bool = False,
) -> str:
    """
    Generate text using local Ollama LLM with automatic structured fallback.
    """
    if not is_ollama_online():
        return _generate_offline_fallback(prompt, system=system, json_mode=json_mode)

    model = model or settings.OLLAMA_MODEL
    url = f"{settings.OLLAMA_BASE_URL}/api/chat"

    payload: dict[str, Any] = {
        "model": model,
        "messages": _build_messages(prompt, system),
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    if json_mode:
        payload["format"] = "json"

    try:
        response = requests.post(url, json=payload, timeout=settings.AI_REQUEST_TIMEOUT_SECONDS)
        if response.status_code < 400:
            data = response.json()
            content = data.get("message", {}).get("content", "").strip()
            if content:
                return content
    except Exception as exc:
        logger.warning("Ollama request failed (%s). Using built-in structured generator.", exc)

    return _generate_offline_fallback(prompt, system=system, json_mode=json_mode)


def generate_text_streaming(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
) -> Generator[str, None, None]:
    """Stream text tokens from local Ollama LLM."""
    if not is_ollama_online():
        yield _generate_offline_fallback(prompt, system=system, json_mode=False)
        return

    model = model or settings.OLLAMA_MODEL
    url = f"{settings.OLLAMA_BASE_URL}/api/chat"

    payload: dict[str, Any] = {
        "model": model,
        "messages": _build_messages(prompt, system),
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }

    try:
        response = requests.post(url, json=payload, stream=True, timeout=10)
        for line in response.iter_lines(decode_unicode=True):
            if line:
                chunk = json.loads(line)
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token
    except Exception as exc:
        logger.warning("Ollama streaming unavailable (%s). Yielding fallback content.", exc)
        yield _generate_offline_fallback(prompt, system=system, json_mode=False)
