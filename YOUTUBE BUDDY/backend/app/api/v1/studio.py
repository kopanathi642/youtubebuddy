"""
Studio API — Production image & text generation endpoint.

Uses professional prompt templates for every tool, saves generated
images to disk, and persists all generations to the database.
"""
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.core.security import get_current_user
from app.models.ai_generation import AIGeneration
from app.schemas.user import UserProfile
from app.services.ai_generation import (
    generate_image_from_prompt,
    generate_studio_text,
    reset_simulation_flag,
    save_generated_image,
    set_simulation_flag,
    was_simulated,
)
from app.services.ownership import require_upload, require_user

router = APIRouter()


class Provider(str, Enum):
    gemini = "gemini"
    groq = "groq"
    openrouter = "openrouter"
    ollama = "ollama"
    openai = "openai"
    huggingface = "huggingface"
    hf = "hf"
    auto = "auto"


class StudioGenerateRequest(BaseModel):
    tool_id: str = Field(min_length=1, max_length=100)
    category: str | None = None
    prompt: str | None = Field(default=None, max_length=6000)
    style: str | None = None
    aspect_ratio: str | None = None
    duration: int | None = None
    provider: Provider = Provider.auto
    upload_id: int | None = None


class StudioGenerateResponse(BaseModel):
    id: int
    tool_id: str
    provider: Provider
    prompt: str | None = None
    style: str | None = None
    preview_url: str | None = None
    generated_text: str | None = None
    model_output: dict | str | None = None
    simulated: bool = False
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "protected_namespaces": (),
    }


IMAGE_TOOLS = {
    "create",
    "cineshot",
    "moodboard",
    "character",
    "persona",
    "aesthetic",
    "relight",
    "inpaint",
    "faceswap",
    "charswap",
    "fashion",
    "upscale",
    "draw",
}


@router.post("/generate", response_model=StudioGenerateResponse)
@router.post("/", response_model=StudioGenerateResponse, include_in_schema=False)
async def generate_tool(
    request: StudioGenerateRequest,
    current_user: UserProfile = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    user = await require_user(session, current_user)
    prompt_text = (request.prompt or "").strip()
    if request.upload_id is not None:
        await require_upload(session, request.upload_id, user)
    if not prompt_text:
        raise HTTPException(422, "Describe the output you want to create.")
    if request.tool_id in {"create", "draw", "upscale"} and request.category is None:
        raise HTTPException(422, "category is required for ambiguous legacy tool IDs.")
    if request.category in {"video", "audio"}:
        raise HTTPException(503, detail={"status":"requires_configuration", "capability":request.category, "message":"No compatible generative model is configured. Text and poster cards are not substitutes for media."})
    if request.tool_id not in {"create", "cineshot", "aesthetic", "fashion", "script", "seo", "cinematic_brief"}:
        raise HTTPException(501, detail={"status":"unavailable", "message":"This specialist editing operation does not have an implemented engine."})
    if request.upload_id is not None:
        raise HTTPException(501, "Reference-guided generation is not implemented by the current adapter.")

    preview_url: str | None = None
    generated_text: str | None = None
    model_output: dict | str | None = None
    reset_simulation_flag()

    try:
        if request.tool_id in IMAGE_TOOLS:
            # Generate image with professional prompt templates
            image_result = generate_image_from_prompt(
                prompt_text,
                provider=request.provider.value,
                tool_id=request.tool_id,
                style=request.style or "cinematic",
                aspect_ratio=request.aspect_ratio or "16:9",
            )

            # Save image to disk
            filename = f"{request.tool_id}_{uuid4().hex[:8]}.png"
            local_path = save_generated_image(image_result, filename)
            from app.services.media_access import signed_media_url
            preview_url = signed_media_url("rendered", filename, user.id)

            generated_text = f"Image generated successfully using {request.provider.value}."
            model_output = {
                "type": "image",
                "url": preview_url,
                "asset_filename": filename,
                "original_url": image_result if image_result.startswith("http") else None,
            }
        else:
            # Text generation with professional prompt templates
            result = generate_studio_text(
                request.tool_id,
                prompt_text,
                provider=request.provider.value,
                style=request.style or "professional",
                duration=str(request.duration or 10),
                aspect_ratio=request.aspect_ratio or "16:9",
            )
            generated_text = result.get("raw", "")
            model_output = result.get("parsed", generated_text)

    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    generation = AIGeneration(
        user_id=user.id,
        upload_id=request.upload_id,
        agent_name=f"studio:{request.tool_id}",
        prompt=prompt_text,
        output=generated_text,
        generation_metadata=json.dumps(
            {
                "tool_id": request.tool_id,
                "provider": request.provider,
                "style": request.style,
                "aspect_ratio": request.aspect_ratio,
                "duration": request.duration,
                "preview_url": preview_url,
                "asset_filename": Path(local_path).name if preview_url else None,
            }
        ),
        status="completed",
    )
    session.add(generation)
    await session.commit()
    await session.refresh(generation)

    return {
        "id": generation.id,
        "tool_id": request.tool_id,
        "provider": request.provider,
        "prompt": prompt_text,
        "style": request.style,
        "preview_url": preview_url,
        "generated_text": generated_text,
        "model_output": model_output,
        "simulated": was_simulated(),
        "status": generation.status,
        "created_at": generation.created_at,
        "updated_at": generation.updated_at,
    }


@router.get("/history")
async def studio_history(
    tool_id: str | None = Query(default=None),
    limit: int = Query(default=20, le=100),
    current_user: UserProfile = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """List past studio generations for the current user."""
    user = await require_user(session, current_user)
    query = (
        select(AIGeneration)
        .where(
            AIGeneration.user_id == user.id,
            AIGeneration.agent_name.startswith("studio:"),
        )
        .order_by(AIGeneration.created_at.desc())
        .limit(limit)
    )
    if tool_id:
        query = query.where(AIGeneration.agent_name == f"studio:{tool_id}")

    result = await session.execute(query)
    generations = result.scalars().all()

    return {
        "data": [
            {
                "id": g.id,
                "tool_id": g.agent_name.replace("studio:", ""),
                "prompt": g.prompt,
                "output_preview": (g.output or "")[:200],
                "status": g.status,
                "created_at": g.created_at,
            }
            for g in generations
        ]
    }


@router.get("/providers")
async def get_providers_status() -> dict:
    """Return health and availability of all AI generation providers."""
    from app.ai.providers.ai_dispatcher import provider_status
    return provider_status()
