import asyncio,json
from pathlib import Path
from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.tool_job import ToolJob
from app.models.upload import Upload
from app.core.config import settings
from app.tools.executor import execute
from app.services.storage import require_safe_upload_path

async def process_job(job_id):
    async with AsyncSessionLocal() as session:
        job=await session.get(ToolJob,job_id)
        if not job or job.status!='queued':return
        upload=await session.get(Upload,job.upload_id)
        if not upload or upload.user_id!=job.user_id:
            job.status='failed';job.error='Source unavailable';await session.commit();return
        job.status='running';await session.commit()
        try:
            source=require_safe_upload_path(upload.storage_path)
            result=await asyncio.to_thread(execute,job.tool_id,source,settings.RENDER_DIR,json.loads(job.options))
            job.result=json.dumps(result);job.status='completed';job.error=None
        except Exception as exc:
            job.status='failed';job.error=str(exc)[:1000]
        await session.commit()

@celery_app.task(name='tools.execute',acks_late=True,soft_time_limit=130,time_limit=140)
def execute_tool_job(job_id):
    asyncio.run(process_job(job_id))
