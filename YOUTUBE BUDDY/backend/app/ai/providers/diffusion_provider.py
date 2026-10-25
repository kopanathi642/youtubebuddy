"""
Stable Diffusion XL Local Image Provider.

Generates high-resolution images using local SDXL weights via diffusers.
Replaces OpenAI DALL-E, HuggingFace Inference API, and Gemini image clients.

Features:
  - SDXL 1024x1024 native generation
  - Aspect ratio mapping (16:9, 9:16, 1:1, 4:5)
  - Negative prompt support
  - Deterministic seed option
  - Base64 data URI and direct file saving
  - Clear availability errors when the local model is not initialized
"""
import base64
import io
import logging
from pathlib import Path
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class ImageGenerationUnavailable(RuntimeError):
    """Raised when a real local image cannot be produced."""

# Aspect ratio dimensions optimized for SDXL (total ~1024x1024 pixels)
ASPECT_RATIO_MAP = {
    "16:9": (1344, 768),
    "9:16": (768, 1344),
    "1:1": (1024, 1024),
    "4:5": (896, 1152),
    "21:9": (1536, 640),
}


def _get_dimensions(aspect_ratio: str) -> tuple[int, int]:
    """Return width and height rounded to multiples of 8 for SDXL."""
    return ASPECT_RATIO_MAP.get(aspect_ratio, (1024, 1024))


def generate_image(
    prompt: str,
    negative_prompt: str | None = None,
    aspect_ratio: str = "16:9",
    num_inference_steps: int = 30,
    guidance_scale: float = 7.5,
    seed: int | None = None,
) -> str:
    """
    Generate an image using local Stable Diffusion XL.

    Returns:
        A data:image/png;base64,... URI string.
    """
    if not settings.LOCAL_IMAGE_MODEL_PATH:
        raise ImageGenerationUnavailable("Configure LOCAL_IMAGE_MODEL_PATH and a compatible GPU runtime. No image was generated.")
    if aspect_ratio not in ASPECT_RATIO_MAP:
        raise ValueError("Unsupported image ratio.")
    width, height = _get_dimensions(aspect_ratio)

    try:
        from app.ai.model_manager import get_diffusion_pipeline
        import torch

        pipe = get_diffusion_pipeline()

        generator = None
        if seed is not None:
            generator = torch.Generator(device=pipe.device).manual_seed(seed)

        logger.info(
            "Generating SDXL image: %dx%d, steps=%d, guidance=%.1f",
            width, height, num_inference_steps, guidance_scale
        )

        with torch.inference_mode():
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt or "ugly, deformed, blurry, low quality, artifacts, watermark",
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
            )

        image = result.images[0]
        buf = io.BytesIO()
        image.save(buf, format="PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{b64}"

    except Exception as exc:
        logger.info("Local SDXL unavailable (%s), attempting high-speed cloud diffusion...", exc)
        try:
            return _generate_cloud_diffusion(prompt=prompt, aspect_ratio=aspect_ratio)
        except Exception as cloud_exc:
            logger.exception("Cloud diffusion also failed: %s", cloud_exc)
            raise ImageGenerationUnavailable(
                "Image generation is unavailable locally and cloud diffusion failed. "
                f"Underlying error: {cloud_exc}"
            ) from cloud_exc


def _generate_cloud_diffusion(prompt: str, aspect_ratio: str = "16:9") -> str:
    raise ImageGenerationUnavailable("Automatic remote image fallback is disabled. Configure a licensed local checkpoint.")

def generate_fallback_image(prompt: str, aspect_ratio: str = "16:9", style: str = "Cinematic Studio") -> str:
    raise ImageGenerationUnavailable("Image model unavailable. Procedural cards are never returned as AI output.")
