"""
Production storage service.

Supports local filesystem storage (development) and Firebase Storage (production).
The active provider is controlled by settings.STORAGE_PROVIDER:
  - 'local'    → files saved to UPLOAD_DIR / RENDER_DIR
  - 'firebase' → files uploaded to Firebase Storage bucket
"""
import logging
from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

logger = logging.getLogger(__name__)

UPLOAD_FOLDER = Path(settings.UPLOAD_DIR)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1 MB

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}
_MAGIC_READ_BYTES = 16


# ── path safety & upload validation ─────────────────────────────────────────

def is_within_directory(base: str | Path, candidate: str | Path) -> bool:
    """True when `candidate` resolves to a location inside `base` (symlink/.. safe)."""
    try:
        Path(candidate).resolve().relative_to(Path(base).resolve())
        return True
    except (ValueError, OSError):
        return False


def require_safe_upload_path(path: str | Path) -> Path:
    """Return the resolved path, or raise 400 if it escapes the upload directory."""
    if not is_within_directory(UPLOAD_FOLDER, path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stored file path is outside the upload directory.",
        )
    return Path(path).resolve()


def _has_video_signature(header: bytes, extension: str) -> bool:
    if extension in {".mp4", ".mov", ".m4v"}:
        return header[4:8] == b"ftyp" or header[4:8] in {b"moov", b"mdat", b"free", b"wide"}
    if extension in {".mkv", ".webm"}:
        return header[:4] == b"\x1a\x45\xdf\xa3"
    if extension == ".avi":
        return header[:4] == b"RIFF" and header[8:12] == b"AVI "
    return False


def validate_extension(filename: str | None) -> str:
    extension = Path(filename or "").suffix.lower()
    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_VIDEO_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed video formats: {allowed}.",
        )
    return extension


async def validate_video_upload(file: UploadFile) -> None:
    """Reject anything that is not a real video container (extension + magic bytes)."""
    extension = validate_extension(file.filename)
    header = await file.read(_MAGIC_READ_BYTES)
    await file.seek(0)
    if not _has_video_signature(header, extension):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="The file content does not look like a valid video.",
        )


# ── filename helpers ────────────────────────────────────────────────────────

def sanitize_filename(filename: str) -> str:
    name = Path(filename).name.strip()
    if not name:
        return "upload"
    safe = "".join(char if char.isalnum() or char in {".", "-", "_"} else "_" for char in name)
    return safe[:180] or "upload"


def build_local_path(filename: str) -> str:
    path = UPLOAD_FOLDER / sanitize_filename(filename)
    return str(path.resolve())


def unique_upload_path(filename: str) -> str:
    safe_name = sanitize_filename(filename)
    path = UPLOAD_FOLDER / f"{uuid4().hex}_{safe_name}"
    return str(path.resolve())


# ── local file operations ───────────────────────────────────────────────────

def save_upload_chunk(chunk_data: bytes, destination: str) -> str:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(chunk_data)
    return str(path)


async def save_upload_file(file: UploadFile, destination: str, max_bytes: int) -> int:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    size = 0

    try:
        async with aiofiles.open(path, "wb") as output:
            while True:
                chunk = await file.read(UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Upload exceeds maximum allowed size of {max_bytes} bytes",
                    )
                await output.write(chunk)
    except Exception:
        if path.exists():
            path.unlink()
        raise
    finally:
        await file.close()

    logger.info("File saved → %s (%d bytes)", path, size)
    return size


def local_upload_path(filename: str) -> str:
    return build_local_path(filename)


# ── cloud storage ───────────────────────────────────────────────────────────

def upload_to_cloud(local_path: str, destination_path: str) -> str:
    """
    Upload a local file to cloud storage.

    When STORAGE_PROVIDER='firebase', uses Firebase Storage.
    Otherwise raises RuntimeError.
    """
    if settings.STORAGE_PROVIDER == "firebase":
        from app.core.firebase import upload_file_to_firebase
        return upload_file_to_firebase(local_path, destination_path)

    raise RuntimeError(
        "Cloud storage is only available when STORAGE_PROVIDER=firebase. "
        "Set STORAGE_PROVIDER=firebase and configure Firebase credentials."
    )


def get_public_url(file_path: str) -> str:
    """
    Return a public URL for a file.

    - Local: returns a relative /uploads/ or /rendered/ URL for backend serving
    - Firebase: returns a Firebase Storage download URL
    """
    if settings.STORAGE_PROVIDER == "firebase":
        from app.core.firebase import get_firebase_download_url
        return get_firebase_download_url(file_path)

    raise RuntimeError("Unscoped local media URLs are disabled. Request an owner-authorized media grant.")


def delete_file(file_path: str) -> bool:
    """Delete a file from local or cloud storage."""
    if settings.STORAGE_PROVIDER == "firebase":
        from app.core.firebase import delete_firebase_file
        return delete_firebase_file(file_path)

    path = Path(file_path)
    if path.exists():
        path.unlink()
        logger.info("Deleted file: %s", path)
        return True
    return False
