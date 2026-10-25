import json, shutil
from uuid import uuid4
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.security import get_current_user
from app.core.config import settings
from app.models.tool_job import ToolJob
from app.schemas.user import UserProfile
from app.services.ownership import require_user,require_upload
from app.services.media_access import signed_media_url
from app.tools.registry import CATALOG,require_tool
router=APIRouter()
class Submit(BaseModel):
    tool_id:str=Field(max_length=180)
    upload_id:int=Field(gt=0)
    request_key:str=Field(min_length=8,max_length=100)
    options:dict=Field(default_factory=dict)
    model_config={'extra':'forbid'}

def payload(job):
    result=json.loads(job.result) if job.result else None
    if result:
        for f in result.get('files',[]):f['url']=signed_media_url('rendered',f['filename'],job.user_id)
    return {'id':job.id,'tool_id':job.tool_id,'status':job.status,'progress':None,'result':result,'error':job.error,'created_at':job.created_at}

@router.get('/catalog')
async def catalog():return CATALOG

@router.get('/runtime')
async def runtime():
    return {'ffmpeg':bool(shutil.which('ffmpeg') and shutil.which('ffprobe')),'background_queue':'requires Redis + a running Celery worker','generative_video':'requires_configuration','always_on_guarantee':False,'paid_inference_enabled':settings.ALLOW_REMOTE_INFERENCE}

@router.post('/jobs',status_code=202)
async def submit(req:Submit,current_user:UserProfile=Depends(get_current_user),session:AsyncSession=Depends(get_session)):
    user=await require_user(session,current_user);await require_upload(session,req.upload_id,user)
    try:tool=require_tool(req.tool_id)
    except ValueError as e:raise HTTPException(404,str(e))
    if tool['engine']!='ffmpeg':raise HTTPException(503,detail={'status':'requires_configuration','message':'This capability has no installed server engine.'})
    previous=await session.scalar(select(ToolJob).where(ToolJob.user_id==user.id,ToolJob.request_key==req.request_key))
    if previous:
        if previous.tool_id!=req.tool_id or previous.upload_id!=req.upload_id or json.loads(previous.options)!=req.options:raise HTTPException(409,'Idempotency key already belongs to different inputs.')
        return payload(previous)
    count=len((await session.execute(select(ToolJob.id).where(ToolJob.user_id==user.id,ToolJob.status.in_(['queued','running'])))).scalars().all())
    if count>=2:raise HTTPException(429,'At most two active jobs per owner.')
    from redis import Redis
    try:Redis.from_url(settings.CELERY_BROKER_URL,socket_connect_timeout=1,socket_timeout=1).ping()
    except Exception:raise HTTPException(503,detail={'status':'requires_configuration','message':'Redis queue is unavailable. Start the configured worker services; no job was queued.'})
    job=ToolJob(id=str(uuid4()),user_id=user.id,upload_id=req.upload_id,tool_id=req.tool_id,request_key=req.request_key,options=json.dumps(req.options),status='queued');session.add(job);await session.commit()
    try:
        from app.workers.tool_tasks import execute_tool_job
        execute_tool_job.apply_async(args=[job.id],task_id='tool-'+job.id,retry=False)
    except Exception:
        job.status='failed';job.error='Queue submission failed; retry with a new request key.';await session.commit();raise HTTPException(503,job.error)
    return payload(job)

@router.get('/jobs')
async def list_jobs(current_user:UserProfile=Depends(get_current_user),session:AsyncSession=Depends(get_session)):
    user=await require_user(session,current_user)
    rows=(await session.execute(select(ToolJob).where(ToolJob.user_id==user.id).order_by(ToolJob.created_at.desc()).limit(100))).scalars().all()
    return {'data':[payload(j) for j in rows]}

@router.post('/jobs/{job_id}/cancel')
async def cancel(job_id:str,current_user:UserProfile=Depends(get_current_user),session:AsyncSession=Depends(get_session)):
    user=await require_user(session,current_user);job=await session.scalar(select(ToolJob).where(ToolJob.id==job_id,ToolJob.user_id==user.id))
    if not job:raise HTTPException(404,'Job not found')
    if job.status!='queued':raise HTTPException(409,'Only queued jobs can be cancelled safely by this worker.')
    job.status='cancelled';await session.commit();return payload(job)
