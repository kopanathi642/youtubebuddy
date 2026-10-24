"""
Production AI Generation Service — Powered by Local AI & LangGraph.

All inference is routed through local pre-trained models:
  - Text & analysis: Ollama (Llama 3.1)
  - Image synthesis: Stable Diffusion XL
  - Multi-step tasks: LangGraph StudioGraph
"""
import json
import logging
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from app.ai.graphs.studio_graph import run_studio_tool
from app.ai.prompt_templates import (
    build_image_prompt,
    build_text_prompt,
    get_negative_prompt,
    get_system_prompt,
)
from app.ai.providers.ai_dispatcher import (
    dispatch_transcription,
    generate_ai_text as generate_local_text,
)
from app.ai.providers.diffusion_provider import generate_image as generate_local_image
from app.core.config import settings

logger = logging.getLogger(__name__)

# ── simulation tracking ─────────────────────────────────────────────────────
_simulated: ContextVar[bool] = ContextVar("ai_simulated", default=False)


def reset_simulation_flag() -> None:
    _simulated.set(False)


def was_simulated() -> bool:
    return _simulated.get()


def set_simulation_flag(value: bool) -> None:
    _simulated.set(value)


def _parse_json_or_text(text: str) -> dict:
    """Clean and parse JSON from model output."""
    if not text:
        return {}
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return {"summary": text}


def _clean_user_prompt(prompt: str) -> str:
    return (prompt or "").strip()[:300]


def generate_mock_image(
    tool_id: str = "create",
    prompt: str = "",
    aspect_ratio: str = "16:9",
    style: str = "Cinematic",
) -> str:
    from app.ai.providers.diffusion_provider import generate_fallback_image
    return generate_fallback_image(prompt, aspect_ratio=aspect_ratio, style=style)


def generate_image_from_prompt(prompt: str, provider: str = "ollama", tool_id: str = "cineshot", **kwargs: Any) -> str:
    if provider not in {"auto", "ollama", "local_sdxl"}:
        from app.ai.providers.errors import UnsupportedCapability
        raise UnsupportedCapability("This image adapter supports installed local SDXL only; text providers cannot generate images.", "image")
    aspect_ratio = kwargs.pop("aspect_ratio", "16:9")
    style = kwargs.pop("style", "cinematic")
    full_prompt = build_image_prompt(tool_id, prompt, aspect_ratio=aspect_ratio, style=style, **kwargs)
    return generate_local_image(full_prompt, negative_prompt=get_negative_prompt(tool_id), aspect_ratio=aspect_ratio)

def save_generated_image(image_url_or_data: str, filename: str) -> str:
    import base64, io, re
    from PIL import Image
    if filename != Path(filename).name or not re.fullmatch(r"[A-Za-z0-9_.-]+\.png",filename):
        raise ValueError("Invalid output filename.")
    if not image_url_or_data.startswith(("data:image/png;base64,","data:image/jpeg;base64,")) or len(image_url_or_data)>45_000_000:
        raise ValueError("Only bounded engine-produced PNG/JPEG bytes are accepted. Arbitrary URL downloads are disabled.")
    data=base64.b64decode(image_url_or_data.split(",",1)[1],validate=True)
    with Image.open(io.BytesIO(data)) as image:image.verify()
    folder=Path(settings.RENDER_DIR);folder.mkdir(parents=True,exist_ok=True)
    path=folder/filename;path.write_bytes(data);return str(path.resolve())


def generate_studio_text(
    tool_id: str,
    user_prompt: str,
    provider: str = "ollama",
    **kwargs: str,
) -> dict[str, Any]:
    """Execute text generation through local Ollama inference."""
    system = get_system_prompt(tool_id)
    prompt = build_text_prompt(tool_id, user_prompt, **kwargs)

    raw = generate_local_text(prompt, system=system, preferred_provider=provider, json_mode=True)
    parsed = _parse_json_or_text(raw)

    return {
        "raw": raw,
        "parsed": parsed,
        "tool_id": tool_id,
        "provider": "ollama",
    }


def analyze_transcript_for_clips(transcript: str, provider: str = "ollama") -> dict:
    from app.ai.graphs.shorts_graph import run_shorts_agent
    return run_shorts_agent(transcript)


def generate_metadata_for_upload(upload_name: str, topic: str, provider: str = "ollama") -> dict:
    from app.ai.graphs.upload_graph import run_upload_agent
    return run_upload_agent(topic, upload_name=upload_name)


def generate_script(topic: str, duration: str = "10", style: str = "educational", provider: str = "ollama") -> dict:
    from app.ai.graphs.script_graph import run_script_agent
    return run_script_agent(topic, duration=duration, style=style)


def generate_seo_package(topic: str, provider: str = "ollama") -> dict:
    from app.ai.graphs.seo_graph import run_seo_agent
    return run_seo_agent(topic)


def generate_trend_report(context: str, provider: str = "ollama") -> dict:
    from app.ai.graphs.trend_graph import run_trend_agent
    return run_trend_agent(context)


def generate_cinematic_brief(scene: str, duration: str = "6", camera: str = "smooth dolly", provider: str = "ollama") -> dict:
    return generate_studio_text("cinematic", scene, duration=duration, camera_movement=camera)
