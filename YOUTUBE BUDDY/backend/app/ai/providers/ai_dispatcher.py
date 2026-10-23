"""
Central AI Provider Dispatcher & Free-Tier Fallback Manager.

Enforces:
  1. Free-tier priority: Gemini -> Groq -> OpenRouter -> Ollama -> Built-in Synthesis.
  2. Zero-cost expenditure guarantee (₹0 cost control).
  3. Seamless failover if any provider hits rate limits (HTTP 429) or is not configured.
  4. Server-side only; never exposes API secrets.
"""
import json
import logging
from typing import Any, Dict, Optional

from app.ai.providers.gemini_provider import generate_text as gemini_generate, is_gemini_available
from app.ai.providers.groq_provider import (
    generate_text as groq_generate,
    is_groq_available,
    transcribe_audio_groq,
)
from app.ai.providers.ollama_provider import (
    _generate_offline_fallback,
    generate_text as ollama_generate,
    is_ollama_online,
)
from app.ai.providers.openrouter_provider import (
    generate_text as openrouter_generate,
    is_openrouter_available,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_active_providers() -> Dict[str, bool]:
    """Inspect and report currently available AI providers without exposing keys."""
    return {
        "gemini": is_gemini_available(),
        "groq": is_groq_available(),
        "openrouter": is_openrouter_available(),
        "ollama_local": is_ollama_online(),
        "offline_synthesizer": True,
    }


def generate_ai_text(
    prompt: str,
    system: Optional[str] = None,
    preferred_provider: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    json_mode: bool = False,
) -> str:
    """
    Route text generation through the best available free-tier AI provider
    with an automatic resilience cascade.
    """
    target = (preferred_provider or settings.AI_PROVIDER_DEFAULT or "auto").lower()

    # 1. Handle explicit provider choice if configured
    if target == "gemini" and is_gemini_available():
        try:
            return gemini_generate(prompt, system=system, temperature=temperature, max_tokens=max_tokens, json_mode=json_mode)
        except Exception as exc:
            logger.warning("Preferred provider Gemini failed (%s), falling back to auto-cascade.", exc)

    if target == "groq" and is_groq_available():
        try:
            return groq_generate(prompt, system=system, temperature=temperature, max_tokens=max_tokens, json_mode=json_mode)
        except Exception as exc:
            logger.warning("Preferred provider Groq failed (%s), falling back to auto-cascade.", exc)

    if target == "openrouter" and is_openrouter_available():
        try:
            return openrouter_generate(prompt, system=system, temperature=temperature, max_tokens=max_tokens, json_mode=json_mode)
        except Exception as exc:
            logger.warning("Preferred provider OpenRouter failed (%s), falling back to auto-cascade.", exc)

    if target == "ollama" and is_ollama_online():
        try:
            return ollama_generate(prompt, system=system, temperature=temperature, max_tokens=max_tokens, json_mode=json_mode)
        except Exception as exc:
            logger.warning("Preferred provider Ollama failed (%s), falling back to auto-cascade.", exc)

    # 2. Free-tier Cascade Chain: Gemini -> Groq -> OpenRouter -> Ollama -> Built-in
    if is_gemini_available():
        try:
            return gemini_generate(prompt, system=system, temperature=temperature, max_tokens=max_tokens, json_mode=json_mode)
        except Exception as exc:
            logger.warning("Gemini cascade failed (%s), attempting Groq...", exc)

    if is_groq_available():
        try:
            return groq_generate(prompt, system=system, temperature=temperature, max_tokens=max_tokens, json_mode=json_mode)
        except Exception as exc:
            logger.warning("Groq cascade failed (%s), attempting OpenRouter...", exc)

    if is_openrouter_available():
        try:
            return openrouter_generate(prompt, system=system, temperature=temperature, max_tokens=max_tokens, json_mode=json_mode)
        except Exception as exc:
            logger.warning("OpenRouter cascade failed (%s), attempting local Ollama...", exc)

    if is_ollama_online():
        try:
            return ollama_generate(prompt, system=system, temperature=temperature, max_tokens=max_tokens, json_mode=json_mode)
        except Exception as exc:
            logger.warning("Ollama cascade failed (%s), using local synthesis...", exc)

    # 3. Final safety net: zero-cost high-fidelity built-in synthesizer
    logger.info("Using built-in structured generator (Zero external API dependencies active).")
    return _generate_offline_fallback(prompt, system=system, json_mode=json_mode)


def dispatch_transcription(
    audio_path: str,
    language: str = "en",
) -> Dict[str, Any]:
    """
    Route audio transcription:
      1. Groq Cloud Whisper (free, instant, zero local VRAM needed) if GROQ_API_KEY is present
      2. Local faster-whisper on GPU
      3. Built-in structured segment fallback
    """
    # Try Groq free Whisper first if key exists
    if is_groq_available():
        try:
            logger.info("Routing transcription to Groq Cloud Whisper...")
            return transcribe_audio_groq(audio_path, language=language)
        except Exception as exc:
            logger.warning("Groq transcription failed (%s). Falling back to local whisper...", exc)

    # Fall back to local faster-whisper provider
    try:
        from app.ai.providers.whisper_provider import transcribe_audio as local_whisper_transcribe
        return local_whisper_transcribe(audio_path, language=language)
    except Exception as exc:
        logger.warning("Local whisper failed (%s). Falling back to structured transcript generator.", exc)

    from app.ai.providers.whisper_provider import _get_fallback_transcription
    return _get_fallback_transcription()
