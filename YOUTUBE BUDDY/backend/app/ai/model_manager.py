"""
GPU Model Lifecycle Manager.

Singleton that loads AI models once at startup and keeps them in GPU memory
for fast inference. Handles:
  - Ollama health checking and model availability
  - Stable Diffusion XL pipeline (loaded once, reused)
  - Faster-Whisper model (loaded once, reused)
  - Graceful shutdown and VRAM cleanup
"""
import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-loaded model singletons — avoid importing heavy libs at module level
# ---------------------------------------------------------------------------
_diffusion_pipeline: Any = None
_whisper_model: Any = None
_lock = threading.Lock()


# ── Ollama (Text Generation) ───────────────────────────────────────────────

def check_ollama_health(base_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama server is running and reachable."""
    import requests

    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def ensure_ollama_model(model: str, base_url: str = "http://localhost:11434") -> bool:
    """Verify a specific model is available in Ollama. Pull if missing."""
    import requests

    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=10)
        if resp.status_code != 200:
            return False
        available = [m.get("name", "") for m in resp.json().get("models", [])]
        # Ollama names may include :latest suffix
        for name in available:
            if model in name:
                return True
        return False  # Installing weights is an explicit owner action.
    except Exception as exc:
        logger.warning("Ollama model check failed: %s", exc)
        return False


# ── Stable Diffusion XL (Image Generation) ─────────────────────────────────

def get_diffusion_pipeline(
    model_id: str = "stabilityai/stable-diffusion-xl-base-1.0",
    device: str = "cuda",
):
    """
    Get or create the Stable Diffusion XL pipeline.

    Loads the model on first call and caches it in GPU memory.
    Thread-safe via a global lock.
    """
    global _diffusion_pipeline

    if _diffusion_pipeline is not None:
        return _diffusion_pipeline

    with _lock:
        # Double-check after acquiring lock
        if _diffusion_pipeline is not None:
            return _diffusion_pipeline

        import torch
        from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler

        logger.info("Loading Stable Diffusion XL pipeline: %s", model_id)

        from app.core.config import settings
        from pathlib import Path
        if not settings.LOCAL_IMAGE_MODEL_PATH or not Path(settings.LOCAL_IMAGE_MODEL_PATH).is_dir():
            raise RuntimeError("Configure LOCAL_IMAGE_MODEL_PATH with an installed licensed checkpoint.")
        model_id = settings.LOCAL_IMAGE_MODEL_PATH
        pipe = StableDiffusionXLPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            use_safetensors=True,
            local_files_only=True,
            variant="fp16",
        )

        # Use fast DPM-Solver++ scheduler for fewer steps
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            pipe.scheduler.config
        )

        pipe = pipe.to(device)

        # Enable memory optimizations
        pipe.enable_attention_slicing()
        try:
            pipe.enable_xformers_memory_efficient_attention()
            logger.info("xformers memory-efficient attention enabled")
        except Exception:
            logger.info("xformers not available — using default attention")

        _diffusion_pipeline = pipe
        logger.info("Stable Diffusion XL loaded on %s", device)
        return _diffusion_pipeline


# ── Faster-Whisper (Audio Transcription) ────────────────────────────────────

def get_whisper_model(
    model_size: str = "large-v3",
    device: str = "cuda",
    compute_type: str = "float16",
):
    """
    Get or create the faster-whisper model.

    Loads on first call and caches for reuse. Thread-safe.
    """
    global _whisper_model

    if _whisper_model is not None:
        return _whisper_model

    with _lock:
        if _whisper_model is not None:
            return _whisper_model

        from faster_whisper import WhisperModel

        logger.info(
            "Loading faster-whisper model: %s (device=%s, compute=%s)",
            model_size, device, compute_type,
        )

        from app.core.config import settings
        from pathlib import Path
        if not settings.LOCAL_WHISPER_MODEL_PATH or not Path(settings.LOCAL_WHISPER_MODEL_PATH).is_dir():
            raise RuntimeError("Configure LOCAL_WHISPER_MODEL_PATH with installed Whisper weights.")
        model_size = settings.LOCAL_WHISPER_MODEL_PATH
        model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            local_files_only=True,
        )

        _whisper_model = model
        logger.info("Faster-whisper model loaded on %s", device)
        return _whisper_model


# ── Cleanup ─────────────────────────────────────────────────────────────────

def unload_all_models() -> None:
    """Release GPU memory for all loaded models. Called on app shutdown."""
    global _diffusion_pipeline, _whisper_model

    with _lock:
        if _diffusion_pipeline is not None:
            del _diffusion_pipeline
            _diffusion_pipeline = None
            logger.info("Diffusion pipeline unloaded")

        if _whisper_model is not None:
            del _whisper_model
            _whisper_model = None
            logger.info("Whisper model unloaded")

    # Force CUDA memory cleanup
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("CUDA cache cleared")
    except ImportError:
        pass


def get_gpu_info() -> dict:
    """Return GPU name, VRAM total/used for health check endpoints."""
    try:
        import torch
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            return {
                "gpu_name": props.name,
                "vram_total_gb": round(props.total_mem / 1e9, 2),
                "vram_used_gb": round(torch.cuda.memory_allocated(0) / 1e9, 2),
                "cuda_version": torch.version.cuda,
            }
    except Exception:
        pass
    return {"gpu_name": "N/A", "vram_total_gb": 0, "vram_used_gb": 0, "cuda_version": "N/A"}
