"""
Google Gemini API Provider (Free Tier).

Free tier quotas:
  - 15 RPM (Requests Per Minute)
  - 1,000,000 Tokens Per Day (TPD)
  - 1,500 Requests Per Day (RPD)
Official API key page: https://aistudio.google.com/apikey

Supports:
  - Structured JSON extraction (response_mime_type="application/json")
  - System role instructions
  - Exponential backoff retry on HTTP 429 / rate limits
"""
import json
import logging
import time
from typing import Any, Dict, Optional

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def is_gemini_available() -> bool:
    """Return True if a non-empty GEMINI_API_KEY is configured."""
    return bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())


def generate_text(
    prompt: str,
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    json_mode: bool = False,
) -> str:
    """
    Generate text using Google Gemini's official REST API with free-tier resilience.
    """
    if not is_gemini_available():
        raise ValueError("GEMINI_API_KEY is not configured in backend/.env")

    model_name = model or settings.GEMINI_MODEL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={settings.GEMINI_API_KEY.strip()}"

    # Build payload
    contents = [
        {
            "role": "user",
            "parts": [{"text": prompt}],
        }
    ]

    generation_config: Dict[str, Any] = {
        "temperature": temperature,
        "maxOutputTokens": max_tokens,
    }

    if json_mode:
        generation_config["responseMimeType"] = "application/json"

    payload: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": generation_config,
    }

    if system:
        payload["systemInstruction"] = {
            "parts": [{"text": system}]
        }

    # Request with exponential retry on 429 rate limit
    max_retries = 3
    backoff = 2.0

    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Calling Gemini API (%s) | prompt_len=%d json_mode=%s attempt=%d", model_name, len(prompt), json_mode, attempt)
            resp = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
            )

            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise RuntimeError("Gemini API returned no candidates.")
                
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    raise RuntimeError("Gemini candidate contains no parts.")

                return parts[0].get("text", "").strip()

            elif resp.status_code == 429:
                logger.warning("Gemini 429 Rate Limit hit. Retrying in %.1fs (attempt %d/%d)", backoff, attempt, max_retries)
                time.sleep(backoff)
                backoff *= 2.0
                continue
            else:
                err_msg = resp.text[:400]
                logger.error("Gemini API error (HTTP %d): %s", resp.status_code, err_msg)
                raise RuntimeError(f"Gemini API returned HTTP {resp.status_code}: {err_msg}")

        except requests.exceptions.Timeout:
            logger.warning("Gemini request timed out on attempt %d", attempt)
            if attempt == max_retries:
                raise
            time.sleep(backoff)
        except requests.exceptions.ConnectionError as exc:
            logger.warning("Gemini connection error: %s", exc)
            if attempt == max_retries:
                raise
            time.sleep(backoff)

    raise RuntimeError("Gemini API request failed after retries.")
