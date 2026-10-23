from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, computed_field

from app.core.config import settings


class ShortRequest(BaseModel):
    upload_id: int | None = Field(default=None, alias="videoId")
    start_seconds: int | None = Field(default=0, alias="startSeconds")
    end_seconds: int | None = Field(default=15, alias="endSeconds")
    ratio: str | None = Field(default="9:16", alias="aspectRatio")
    caption_style: str | None = Field(default=None, alias="captionStyle")
    captions: bool | None = Field(default=None)
    auto_detect: bool | None = Field(default=None, alias="autoDetect")

    model_config = {
        "populate_by_name": True,
    }


class ShortResponse(BaseModel):
    id: int
    upload_id: int
    user_id: int
    ratio: str
    clip_start: int
    clip_end: int
    # Used only to derive `url`; never serialised (it is an absolute server path).
    storage_path: str = Field(exclude=True)
    status: str
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url(self) -> str:
        return f"{settings.BACKEND_HOST.rstrip('/')}/rendered/{Path(self.storage_path).name}"

    model_config = {
        "from_attributes": True,
    }
