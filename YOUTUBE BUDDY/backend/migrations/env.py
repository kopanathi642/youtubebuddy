import asyncio
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.models import Base
config=context.config
target_metadata=Base.metadata

def run(connection):
    context.configure(connection=connection,target_metadata=target_metadata,compare_type=True)
    with context.begin_transaction():context.run_migrations()

async def online():
    engine=create_async_engine(config.get_main_option('sqlalchemy.url') or settings.DATABASE_URL)
    async with engine.connect() as connection:await connection.run_sync(run)
    await engine.dispose()

if context.is_offline_mode():
    context.configure(url=config.get_main_option('sqlalchemy.url') or settings.DATABASE_URL,target_metadata=target_metadata,literal_binds=True)
    with context.begin_transaction():context.run_migrations()
else:asyncio.run(online())
