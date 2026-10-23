"""
Whisper transcription utility — delegates to multi-provider audio dispatcher (Groq Whisper / Faster-Whisper).
"""
from app.ai.providers.ai_dispatcher import dispatch_transcription as transcribe_audio
from app.ai.providers.whisper_provider import (
    extract_timestamps,
    extract_word_timestamps,
    generate_srt_from_segments,
    generate_vtt_from_segments,
)

__all__ = [
    "transcribe_audio",
    "extract_timestamps",
    "extract_word_timestamps",
    "generate_srt_from_segments",
    "generate_vtt_from_segments",
]
