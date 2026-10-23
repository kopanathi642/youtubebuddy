"""
Groq API Provider (Free Tier).

Free tier quotas:
  - 30 RPM (Requests Per Minute)
  - 14,400 RPD (Requests Per Day)
  - Ultra-fast inference (300-800 tokens/sec)
Official API key page: https://console.groq.com/keys

Supports:
  - Fast text & script generation (LLaMA 3.3 70B & 3.1 8B)
  - Speech-to-text via Groq Whisper (whisper-large-v3-turbo)
  - Structured JSON format
"""
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_TRANSCRIPTION_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


def is_groq_available() -> bool:
    """Return True if a non-empty GROQ_API_KEY is configured."""
    return bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY.strip())


def generate_text(
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    json_mode: bool = False,
) -> str:
    """
    Generate text using Groq's high-speed free-tier endpoint.
    """
    if not is_groq_available():
        raise ValueError("GROQ_API_KEY is not configured in backend/.env")

    model_name = model or settings.GROQ_MODEL
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY.strip()}",
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

    max_retries = 3
    backoff = 1.5

    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Calling Groq API (%s) | prompt_len=%d attempt=%d", model_name, len(prompt), attempt)
            resp = requests.post(
                GROQ_CHAT_URL,
                headers=headers,
                json=payload,
                timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
            )

            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
                raise RuntimeError("Groq API returned empty choices.")

            elif resp.status_code == 429:
                logger.warning("Groq rate limit hit. Waiting %.1fs (attempt %d/%d)", backoff, attempt, max_retries)
                time.sleep(backoff)
                backoff *= 2.0
                continue
            else:
                err_msg = resp.text[:400]
                logger.error("Groq API error (HTTP %d): %s", resp.status_code, err_msg)
                raise RuntimeError(f"Groq API returned HTTP {resp.status_code}: {err_msg}")

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            logger.warning("Groq network issue on attempt %d: %s", attempt, exc)
            if attempt == max_retries:
                raise
            time.sleep(backoff)

    raise RuntimeError("Groq API request failed after retries.")


def transcribe_audio_groq(
    audio_path: str,
    language: str = "en",
) -> Dict[str, Any]:
    """
    Transcribe audio file using Groq's free cloud Whisper endpoint.
    """
    if not is_groq_available():
        raise ValueError("GROQ_API_KEY is not configured for Groq transcription")

    file_path = Path(audio_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY.strip()}",
    }

    with open(file_path, "rb") as f:
        files = {
            "file": (file_path.name, f, "audio/mpeg"),
        }
        data = {
            "model": settings.GROQ_WHISPER_MODEL,
            "response_format": "verbose_json",
            "language": language if language != "auto" else "en",
        }

        resp = requests.post(GROQ_TRANSCRIPTION_URL, headers=headers, files=files, data=data, timeout=120)
        if resp.status_code == 200:
            result = resp.json()
            return {
                "text": result.get("text", "").strip(),
                "duration": result.get("duration", 0.0),
                "language": result.get("language", language),
                "segments": result.get("segments", []),
                "simulated": False,
                "provider": "groq-whisper",
            }
        else:
            raise RuntimeError(f"Groq Whisper transcription failed (HTTP {resp.status_code}): {resp.text[:300]}")
