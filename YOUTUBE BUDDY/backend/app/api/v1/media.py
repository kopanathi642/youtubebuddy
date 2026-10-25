import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.security import get_current_user
from app.schemas.user import UserProfile
from app.models.user import User
from app.models.tool_job import ToolJob
from app.models.upload import Upload
from app.models.short import Short
from app.models.render_job import RenderJob
from app.models.ai_generation import AIGeneration
from app.services.ownership import require_user, require_upload
from app.services.media_access import safe_media_path, signed_media_url, verify_media_grant
router=APIRouter()

@router.get('/upload-access/{upload_id}')
async def upload_access(upload_id:int,current_user:UserProfile=Depends(get_current_user),session:AsyncSession=Depends(get_session)):
    user=await require_user(session,current_user);upload=await require_upload(session,upload_id,user)
    return {'url':signed_media_url('uploads',Path(upload.storage_path).name,user.id),'expires_in':300}

@router.get('/{kind}/{filename}')
async def read_media(kind:str,filename:str,token:str=Query(min_length=1),session:AsyncSession=Depends(get_session)):
    path=safe_media_path(kind,filename);owner_id=verify_media_grant(token,kind,filename)
    user=await session.get(User,owner_id)
    if not user or not user.is_active:raise HTTPException(404,'Media not found')
    authorized=False
    models=[Upload] if kind=='uploads' else [Short,RenderJob]
    for model in models:
        attr=model.storage_path if model in {Upload,Short} else model.result_path
        rows=(await session.execute(select(attr).where(model.user_id==owner_id))).scalars().all()
        if any(raw and Path(raw).resolve()==path for raw in rows):authorized=True;break
    if not authorized and kind=='rendered':
        rows=(await session.execute(select(AIGeneration.generation_metadata).where(AIGeneration.user_id==owner_id))).scalars().all()
        for raw in rows:
            try:meta=json.loads(raw or '{}')
            except (ValueError,TypeError):continue
            if meta.get('asset_filename')==filename:authorized=True;break
    if not authorized and kind=='rendered':
        jobs=(await session.execute(select(ToolJob.result).where(ToolJob.user_id==owner_id,ToolJob.status=='completed'))).scalars().all()
        for raw in jobs:
            try:files=json.loads(raw or '{}').get('files',[])
            except (ValueError,TypeError):continue
            if any(f.get('filename')==filename for f in files):authorized=True;break
    if not authorized or not path.is_file():raise HTTPException(404,'Media not found')
    return FileResponse(path,headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'})
