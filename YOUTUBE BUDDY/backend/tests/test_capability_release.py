"""Real CPU outputs and security contracts. No model result is mocked as verified inference."""
import json,subprocess
from pathlib import Path
import pytest
from fastapi import HTTPException
from app.tools.registry import CATALOG,TOOLS
from app.tools.executor import execute,probe
from app.services.media_access import signed_media_url,verify_media_grant,safe_media_path
from app.ai.providers.errors import ProviderUnavailable

@pytest.mark.parametrize('tool',CATALOG['tools'],ids=lambda t:t['id'])
def test_every_catalog_contract(tool):
    assert tool['id'].count('.')>=1
    assert tool['status'] in {'implemented','planned','requires_configuration'}
    assert tool['inputs']['type']=='object' and tool['outputs']['type']=='object'
    assert tool['requirements'] and tool['tests'] and tool['permissions'] and tool['limits']
    if tool['status']!='implemented':assert tool['engine']=='not_installed' and tool['configuration']

def test_no_duplicate_capabilities():assert len(TOOLS)==360

@pytest.fixture(scope='module')
def real_video(tmp_path_factory):
    p=tmp_path_factory.mktemp('source')/'fixture.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc=size=320x180:rate=12','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','2','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(p)],check=True,timeout=20)
    return p

@pytest.mark.parametrize('tool,options',[
 ('video.trim_split',{'ranges':[[0,.5],[.5,1.5]]}),('video.slow_motion',{'speed':.5}),('video.freeze_frame',{'at':.5}),('video.crop_portrait',{}),('video.crop_square',{}),('video.crop_landscape',{}),('audio.normalize',{}),('media.inspect',{}),('media.validate_ratio',{'ratio':'16:9'}),('media.check_corruption',{}),('media.validate_export',{})])
def test_each_implemented_cpu_engine(tool,options,real_video,tmp_path):
    result=execute(tool,real_video,tmp_path,options)
    assert isinstance(result['metadata'],dict)
    for f in result['files']:
        p=tmp_path/f['filename'];assert p.is_file() and p.stat().st_size==f['bytes']
        if p.suffix!='.png':assert probe(p)['streams']
    if tool=='video.trim_split':assert len(result['files'])==2
    if tool=='video.crop_portrait':
        v=next(x for x in probe(tmp_path/result['files'][0]['filename'])['streams'] if x['codec_type']=='video');assert abs(v['width']/v['height']-9/16)<.02
    if tool=='video.slow_motion':assert float(probe(tmp_path/result['files'][0]['filename'])['format']['duration'])>3.5

@pytest.mark.parametrize('tool',[t['id'] for t in CATALOG['tools'] if t['engine']=='not_installed'])
def test_unimplemented_capability_never_runs(tool,tmp_path):
    with pytest.raises(ProviderUnavailable):execute(tool,tmp_path/'nonexistent.mp4',tmp_path)

def test_invalid_ranges_and_options(real_video,tmp_path):
    with pytest.raises(ValueError):execute('video.trim_split',real_video,tmp_path,{'ranges':[[1,0]]})
    with pytest.raises(ValueError):execute('video.slow_motion',real_video,tmp_path,{'speed':float('nan')})
    with pytest.raises(ValueError):execute('media.inspect',real_video,tmp_path,{'shell':'bad'})

def test_no_canned_outputs():
    from app.ai.providers.ollama_provider import _generate_offline_fallback
    from app.ai.providers.whisper_provider import _get_fallback_transcription
    from app.ai.providers.diffusion_provider import generate_fallback_image
    with pytest.raises(ProviderUnavailable):_generate_offline_fallback('test')
    with pytest.raises(ProviderUnavailable):_get_fallback_transcription()
    with pytest.raises(RuntimeError):generate_fallback_image('test')

def test_media_grant_is_scoped_and_expiring():
    from urllib.parse import parse_qs,urlsplit
    url=signed_media_url('rendered','owned.mp4',42)
    token=parse_qs(urlsplit(url).query)['token'][0]
    assert verify_media_grant(token,'rendered','owned.mp4')==42
    with pytest.raises(HTTPException):verify_media_grant(token,'rendered','someone-else.mp4')
    with pytest.raises(HTTPException):verify_media_grant(token+'x','rendered','owned.mp4')
    with pytest.raises(HTTPException):safe_media_path('uploads','../private.mp4')

def test_invalid_token_never_becomes_demo_user(monkeypatch):
    from app.core.config import settings
    from app.core.security import token_to_profile
    monkeypatch.setattr(settings,'ENABLE_DEMO_LOGIN',True)
    with pytest.raises(HTTPException):token_to_profile('not-a-valid-token')

def test_schema_migration_preserves_existing_rows(tmp_path):
    import sqlite3
    from alembic.config import Config
    from alembic import command
    config=Config(str(Path(__file__).resolve().parents[1]/'alembic.ini'));db=tmp_path/'migration.db';config.set_main_option('sqlalchemy.url',f'sqlite+aiosqlite:///{db}')
    command.upgrade(config,'0001')
    with sqlite3.connect(db) as conn:conn.execute("INSERT INTO users (uid,email,provider,is_active) VALUES ('migration-owner','migration@example.test','local',1)")
    command.upgrade(config,'head')
    with sqlite3.connect(db) as conn:
        assert conn.execute('SELECT count(*) FROM users').fetchone()[0]==1
        assert conn.execute("SELECT name FROM sqlite_master WHERE name='tool_jobs'").fetchone()
    command.downgrade(config,'0001')
    with sqlite3.connect(db) as conn:assert conn.execute('SELECT count(*) FROM users').fetchone()[0]==1

@pytest.mark.asyncio
async def test_private_media_rechecks_ownership(session,test_user,test_project,tmp_path,monkeypatch):
    import httpx
    from app.main import app
    from app.core.database import get_session
    from app.core.config import settings
    from app.models.user import User
    from app.models.upload import Upload
    from urllib.parse import urlsplit
    monkeypatch.setattr(settings,'UPLOAD_DIR',str(tmp_path))
    path=tmp_path/'owned.mp4';path.write_bytes(b'private-source-content')
    other=User(uid='other-reader',email='other-reader@example.test',provider='local',is_active=True);session.add(other);await session.flush()
    session.add(Upload(project_id=test_project.id,user_id=test_user.id,filename=path.name,content_type='video/mp4',storage_path=str(path)));await session.flush()
    async def override():yield session
    app.dependency_overrides[get_session]=override
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            good=urlsplit(signed_media_url('uploads',path.name,test_user.id));bad=urlsplit(signed_media_url('uploads',path.name,other.id))
            assert (await client.get(good.path+'?'+good.query)).status_code==200
            assert (await client.get(bad.path+'?'+bad.query)).status_code==404
            assert (await client.get('/uploads/'+path.name)).status_code==404
    finally:app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_existing_demo_password_and_token_do_not_work_when_demo_disabled(session,monkeypatch):
    from app.core.config import settings
    from app.services.auth import authenticate_user,hash_password
    from app.core.security import get_current_user,create_access_token
    from fastapi.security import HTTPAuthorizationCredentials
    from app.models.user import User
    monkeypatch.setattr(settings,'ENABLE_DEMO_LOGIN',False)
    user=User(uid='demo-user-123',email=settings.DEMO_LOGIN_EMAIL,password_hash=hash_password(settings.DEMO_LOGIN_PASSWORD),provider='local',is_active=True)
    session.add(user);await session.flush()
    assert await authenticate_user(session,settings.DEMO_LOGIN_EMAIL,settings.DEMO_LOGIN_PASSWORD) is None
    token=create_access_token(user.uid,additional_claims={'email':user.email})
    with pytest.raises(HTTPException):await get_current_user(HTTPAuthorizationCredentials(scheme='Bearer',credentials=token))
