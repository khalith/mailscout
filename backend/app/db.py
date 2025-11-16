# backend/app/db.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings
from pydantic_settings import BaseSettings

# IMPORTANT — define Base here so Alembic can see metadata
Base = declarative_base()

# Async engine
# engine = create_async_engine(
#     str(settings.DATABASE_URL),
#     pool_pre_ping=True,
#     echo=settings.DEBUG,
#     future=True,
# )
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG if hasattr(settings, "DEBUG") else True,
)

# Session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# FastAPI dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
