"""
Faster-Whisper Local Audio Transcription Provider.

High-throughput, GPU-accelerated local audio transcription using faster-whisper.
Replaces OpenAI Whisper-1 API and HuggingFace Whisper inference endpoints.

Features:
  - GPU accelerated FP16 inference
  - Word-level and segment-level timestamps
  - SRT and WebVTT caption generator
  - Simulation fallback for testing/graceful degradation
"""
import logging
from pathlib import Path
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


def _format_timestamp(seconds: float, separator: str = ",") -> str:
    """Format seconds into HH:MM:SS,mmm (SRT) or HH:MM:SS.mmm (VTT)."""
    total = float(seconds)
    millis = int((total - int(total)) * 1000)
    total_int = int(total)
    hours = total_int // 3600
    minutes = (total_int % 3600) // 60
    secs = total_int % 60
    return f"{hours:02}:{minutes:02}:{secs:02}{separator}{millis:03}"


def transcribe_audio(
    audio_path: str,
    language: str = "en",
    beam_size: int = 5,
    word_timestamps: bool = True,
) -> dict[str, Any]:
    """
    Transcribe audio file using local faster-whisper model.

    Returns:
        Dict with text, segments, words, and duration.
    """
    audio_file = Path(audio_path)
    if not audio_file.exists():
        logger.warning("Audio file not found at %s, returning simulated transcription", audio_path)
        return _get_fallback_transcription()

    try:
        from app.ai.model_manager import get_whisper_model

        model = get_whisper_model()
        logger.info("Transcribing audio locally with faster-whisper: %s", audio_path)

        segments_iter, info = model.transcribe(
            str(audio_file),
            language=language if language != "auto" else None,
            beam_size=beam_size,
            word_timestamps=word_timestamps,
        )

        all_text: list[str] = []
        segments: list[dict[str, Any]] = []

        for seg in segments_iter:
            all_text.append(seg.text.strip())
            words_list = []
            if word_timestamps and hasattr(seg, "words") and seg.words:
                for w in seg.words:
                    words_list.append({
                        "word": w.word.strip(),
                        "start": round(w.start, 2),
                        "end": round(w.end, 2),
                        "probability": round(w.probability, 2),
                    })

            segments.append({
                "id": seg.id,
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
                "words": words_list,
            })

        full_text = " ".join(all_text)
        return {
            "text": full_text,
            "duration": round(info.duration, 2),
            "language": info.language,
            "segments": segments,
            "simulated": False,
        }

    except Exception as exc:
        logger.warning(
            "faster-whisper inference failed or not installed (%s). Using fallback transcription.",
            exc,
        )
        return _get_fallback_transcription()


def _get_fallback_transcription() -> dict[str, Any]:
    from app.ai.providers.errors import ProviderUnavailable
    raise ProviderUnavailable("Transcription requires installed Whisper weights and a compatible runtime. No transcript was generated.", "transcription")

def extract_timestamps(transcript_response: dict) -> list[dict]:
    """Extract structured timestamp segments from a transcription response."""
    segments = transcript_response.get("segments", [])
    return [
        {
            "start": segment.get("start"),
            "end": segment.get("end"),
            "text": segment.get("text"),
        }
        for segment in segments
        if segment.get("text")
    ]


def extract_word_timestamps(transcript_response: dict) -> list[dict]:
    """Extract word-level timestamps (when available from Whisper)."""
    words = []
    for segment in transcript_response.get("segments", []):
        for word_info in segment.get("words", []):
            words.append({
                "word": word_info.get("word", "").strip(),
                "start": word_info.get("start"),
                "end": word_info.get("end"),
            })
    return words


def generate_srt_from_segments(segments: list[dict]) -> str:
    """Generate SRT subtitle content from timestamp segments."""
    lines = []
    for i, seg in enumerate(segments, 1):
        start = _format_timestamp(seg.get("start", 0), separator=",")
        end = _format_timestamp(seg.get("end", 0), separator=",")
        text = seg.get("text", "").strip()
        if text:
            lines.append(f"{i}")
            lines.append(f"{start} --> {end}")
            lines.append(text)
            lines.append("")
    return "\n".join(lines)


def generate_vtt_from_segments(segments: list[dict]) -> str:
    """Generate WebVTT subtitle content from timestamp segments."""
    lines = ["WEBVTT", ""]
    for seg in segments:
        start = _format_timestamp(seg.get("start", 0), separator=".")
        end = _format_timestamp(seg.get("end", 0), separator=".")
        text = seg.get("text", "").strip()
        if text:
            lines.append(f"{start} --> {end}")
            lines.append(text)
            lines.append("")
    return "\n".join(lines)
