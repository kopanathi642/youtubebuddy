"""Local and Free-Tier AI Model Providers."""
from app.ai.providers.ai_dispatcher import (
    dispatch_transcription,
    generate_ai_text,
    get_active_providers,
)
from app.ai.providers.diffusion_provider import generate_image
from app.ai.providers.gemini_provider import generate_text as generate_gemini_text, is_gemini_available
from app.ai.providers.groq_provider import generate_text as generate_groq_text, is_groq_available
from app.ai.providers.ollama_provider import generate_text as generate_ollama_text, is_ollama_online
from app.ai.providers.openrouter_provider import generate_text as generate_openrouter_text, is_openrouter_available
from app.ai.providers.whisper_provider import extract_timestamps, transcribe_audio

__all__ = [
    "generate_ai_text",
    "dispatch_transcription",
    "get_active_providers",
    "generate_image",
    "generate_gemini_text",
    "generate_groq_text",
    "generate_openrouter_text",
    "generate_ollama_text",
    "is_gemini_available",
    "is_groq_available",
    "is_openrouter_available",
    "is_ollama_online",
    "transcribe_audio",
    "extract_timestamps",
]
