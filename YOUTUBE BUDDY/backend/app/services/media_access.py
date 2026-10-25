"""Short-lived, resource-scoped media grants. Never emit unscoped public file URLs."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from jose import jwt, JWTError
from fastapi import HTTPException
from app.core.config import settings

KINDS={'uploads','rendered'}

def safe_media_path(kind: str, filename: str) -> Path:
    if kind not in KINDS or filename!=Path(filename).name or filename in {'','.','..'} or '\\' in filename:
        raise HTTPException(404,'Media not found')
    base=Path(settings.UPLOAD_DIR if kind=='uploads' else settings.RENDER_DIR).resolve()
    path=(base/filename).resolve()
    if path.parent!=base:raise HTTPException(404,'Media not found')
    return path

def signed_media_url(kind: str, filename: str, owner_id: int, seconds: int=300) -> str:
    safe_media_path(kind,filename)
    token=jwt.encode({'sub':str(owner_id),'kind':kind,'filename':filename,'purpose':'media-read','exp':datetime.now(timezone.utc)+timedelta(seconds=min(600,max(1,seconds)))},settings.JWT_SECRET_KEY,algorithm=settings.JWT_ALGORITHM)
    return f'{settings.BACKEND_HOST.rstrip("/")}{settings.API_PREFIX}/media/{kind}/{filename}?'+urlencode({'token':token})

def verify_media_grant(token: str, kind: str, filename: str) -> int:
    try:
        p=jwt.decode(token,settings.JWT_SECRET_KEY,algorithms=[settings.JWT_ALGORITHM],options={'require_exp':True,'require_sub':True})
        if p.get('purpose')!='media-read' or p.get('kind')!=kind or p.get('filename')!=filename:raise ValueError('Wrong resource')
        return int(p['sub'])
    except (JWTError,ValueError,KeyError):raise HTTPException(401,'Invalid or expired media grant')
