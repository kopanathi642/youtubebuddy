from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Configure engine based on database type
engine_kwargs = {
    "echo": False,
    "future": True,
    "pool_pre_ping": True,
}

# Only add pooling parameters for non-SQLite databases
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "pool_size": 10,  # Connection pool size
        "max_overflow": 20,  # Max overflow connections
        "pool_recycle": 3600,  # Recycle connections after 1 hour
    })

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    future=True,
)

async def init_db() -> None:
    from app.models import base

    if settings.ENVIRONMENT.lower() == "production":
        from sqlalchemy import inspect
        async with engine.connect() as conn:
            tables = await conn.run_sync(lambda c: set(inspect(c).get_table_names()))
        if not {"users", "uploads", "tool_jobs", "alembic_version"}.issubset(tables):
            raise RuntimeError("Production schema is not migrated. Run the documented Alembic migration workflow.")
        return
    async with engine.begin() as conn:
        await conn.run_sync(base.Base.metadata.create_all)

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
