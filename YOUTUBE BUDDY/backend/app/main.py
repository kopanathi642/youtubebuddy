from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from app.ai.providers.errors import ProviderUnavailable

from app.ai.model_manager import get_gpu_info, unload_all_models
from app.api.v1 import (
    agents,
    analytics,
    auth,
    captions,
    cinematic,
    render_queue,
    shorts,
    social,
    studio,
    transcription,
    uploads,
    videos,
)
from app.api.v1.users import router as users_router
from app.api.v1 import media, tools
from app.core.cache import close_cache, init_cache
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
)

@app.exception_handler(ProviderUnavailable)
async def unavailable_handler(request, exc):
    return JSONResponse(status_code=503, content={"detail":{"status":exc.status,"capability":exc.capability,"message":str(exc)}})

@app.middleware("http")
async def private_api_headers(request, call_next):
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['X-Frame-Options']='DENY'
    if request.url.path.startswith(settings.API_PREFIX):response.headers['Cache-Control']='private, no-store'
    return response

# ── Middleware ───────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Static file serving for generated content ───────────────────────────────

_upload_dir = Path(settings.UPLOAD_DIR)
_render_dir = Path(settings.RENDER_DIR)
_upload_dir.mkdir(parents=True, exist_ok=True)
_render_dir.mkdir(parents=True, exist_ok=True)
# Source and rendered media are served only through scoped media grants.

# ── API Routes ──────────────────────────────────────────────────────────────

app.include_router(tools.router, prefix=f"{settings.API_PREFIX}/tools", tags=["tools"])
app.include_router(media.router, prefix=f"{settings.API_PREFIX}/media", tags=["media"])
app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["auth"])
app.include_router(users_router, prefix=f"{settings.API_PREFIX}/user", tags=["user"])
app.include_router(uploads.router, prefix=f"{settings.API_PREFIX}/uploads", tags=["uploads"])
app.include_router(videos.router, prefix=f"{settings.API_PREFIX}/videos", tags=["videos"])
app.include_router(transcription.router, prefix=f"{settings.API_PREFIX}/transcription", tags=["transcription"])
app.include_router(shorts.router, prefix=f"{settings.API_PREFIX}/shorts", tags=["shorts"])
app.include_router(cinematic.router, prefix=f"{settings.API_PREFIX}/cinematic", tags=["cinematic"])
app.include_router(studio.router, prefix=f"{settings.API_PREFIX}/studio", tags=["studio"])
app.include_router(captions.router, prefix=f"{settings.API_PREFIX}/captions", tags=["captions"])
app.include_router(agents.router, prefix=f"{settings.API_PREFIX}/agents", tags=["agents"])
app.include_router(social.router, prefix=f"{settings.API_PREFIX}/social", tags=["social"])
app.include_router(analytics.router, prefix=f"{settings.API_PREFIX}/analytics", tags=["analytics"])
app.include_router(render_queue.router, prefix=f"{settings.API_PREFIX}/render-queue", tags=["render-queue"])

# ── Lifecycle events ────────────────────────────────────────────────────────


@app.on_event("startup")
async def startup_event():
    setup_logging()
    settings.validate_production_security()
    await init_db()
    await init_cache()


@app.on_event("shutdown")
async def shutdown_event():
    await close_cache()
    unload_all_models()


# ── Health check ─────────────────────────────────────────────────────────────


@app.get("/healthz")
async def health_check():
    from app.ai.providers import get_active_providers
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "ai_engine": "configured-adapters; no free-compute guarantee",
        "providers": get_active_providers(),
        "gpu": get_gpu_info(),
    }
