from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, computed_field

from app.core.config import settings


class UploadCreate(BaseModel):
    project_id: int | None = None
    filename: str
    content_type: str
    size_bytes: int
    duration_seconds: int | None = None
    storage_path: str


class UploadResponse(BaseModel):
    id: int
    project_id: int
    user_id: int
    filename: str
    content_type: str
    # Used only to derive `url`; never serialised (it is an absolute server path).
    storage_path: str = Field(exclude=True)
    preview_url: str | None = None
    duration_seconds: int | None = None
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url(self) -> str:
        return f"{settings.BACKEND_HOST.rstrip('/')}/uploads/{Path(self.storage_path).name}"

    model_config = {
        "from_attributes": True,
    }
