from datetime import datetime
from sqlalchemy import Column,String,Integer,Text,DateTime,ForeignKey,UniqueConstraint,Index
from app.models.base import Base
class ToolJob(Base):
    __tablename__='tool_jobs'
    __table_args__=(UniqueConstraint('user_id','request_key',name='uq_tool_job_owner_request'),Index('ix_tool_job_owner_status','user_id','status'))
    id=Column(String(36),primary_key=True)
    user_id=Column(Integer,ForeignKey('users.id',ondelete='CASCADE'),nullable=False)
    upload_id=Column(Integer,ForeignKey('uploads.id',ondelete='CASCADE'),nullable=False)
    tool_id=Column(String(180),nullable=False)
    request_key=Column(String(100),nullable=False)
    options=Column(Text,nullable=False,default='{}')
    status=Column(String(40),nullable=False,default='queued')
    result=Column(Text,nullable=True)
    error=Column(Text,nullable=True)
    created_at=Column(DateTime,default=datetime.utcnow,nullable=False)
    updated_at=Column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow,nullable=False)
