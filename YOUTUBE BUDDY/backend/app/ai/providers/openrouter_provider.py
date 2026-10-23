"""
OpenRouter API Provider (Free Tier Compatible Models).

Official API key page: https://openrouter.ai/keys
Accesses available free models (e.g. meta-llama/llama-3.2-3b-instruct:free).
"""
import logging
import time
from typing import Any, Dict, Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def is_openrouter_available() -> bool:
    """Return True if a non-empty OPENROUTER_API_KEY is configured."""
    return bool(settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY.strip())


def generate_text(
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    json_mode: bool = False,
) -> str:
    """
    Generate text using OpenRouter's free-tier eligible models.
    """
    if not is_openrouter_available():
        raise ValueError("OPENROUTER_API_KEY is not configured in backend/.env")

    model_name = model or settings.OPENROUTER_MODEL
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY.strip()}",
        "HTTP-Referer": "https://youtubebuddy.ai",
        "X-Title": "YouTube Buddy",
        "Content-Type": "application/json",
    }

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload: Dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    max_retries = 2
    backoff = 2.0

    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Calling OpenRouter API (%s) | attempt=%d", model_name, attempt)
            resp = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
            )

            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
                raise RuntimeError("OpenRouter returned empty choices.")

            elif resp.status_code == 429:
                logger.warning("OpenRouter rate limit hit. Waiting %.1fs", backoff)
                time.sleep(backoff)
                backoff *= 2.0
                continue
            else:
                err_msg = resp.text[:400]
                logger.error("OpenRouter error (HTTP %d): %s", resp.status_code, err_msg)
                raise RuntimeError(f"OpenRouter returned HTTP {resp.status_code}: {err_msg}")

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            logger.warning("OpenRouter network issue on attempt %d: %s", attempt, exc)
            if attempt == max_retries:
                raise
            time.sleep(backoff)

    raise RuntimeError("OpenRouter API request failed after retries.")
