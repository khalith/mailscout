# backend/app/db.py

import logging
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings
from sqlalchemy.exc import OperationalError
import sqlalchemy

from .config import settings

logger = logging.getLogger("mailscout.db")

# ---------------------------------------------------------
# Define Base (needed by Alembic)
# ---------------------------------------------------------
Base = declarative_base()

# ---------------------------------------------------------
# Lazy engine + Lazy session maker
# ---------------------------------------------------------
_engine = None
_session_maker = None
_AsyncSessionLocal = None   # for backward compatibility


def get_engine():
    """Lazy async engine creation."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=bool(settings.DEBUG),
            future=True,
        )
    return _engine


def get_session_maker():
    """Lazy sessionmaker creation."""
    global _session_maker
    if _session_maker is None:
        _session_maker = sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_maker


# ---------------------------------------------------------
# BACKWARD COMPATIBILITY FOR OLD WORKER IMPORTS
# ---------------------------------------------------------
def _init_async_session_local():
    """
    The old name AsyncSessionLocal should continue to work.
    This wraps get_session_maker() lazily.
    """
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = get_session_maker()
    return _AsyncSessionLocal


# OLD PUBLIC NAME (worker.py uses this)
AsyncSessionLocal = _init_async_session_local


# ---------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------
async def get_db():
    SessionLocal = _init_async_session_local()
    async with SessionLocal() as session:
        yield session


async def get_session():
    """
    Optional duplicate helper (if some parts use this name).
    """
    SessionLocal = get_session_maker()
    async with SessionLocal() as session:
        yield session


# ---------------------------------------------------------
# DB readiness check for Fly.io startup
# ---------------------------------------------------------
async def wait_for_db(max_retries: int = 8, delay: float = 2.0):
    """
    Wait for DB to accept connections — useful for Fly.io startup.
    """
    engine = get_engine()   # <-- Important: use lazy engine

    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(sqlalchemy.text("SELECT 1"))
                logger.info("Database connected (attempt %d)", attempt)
                return True

        except OperationalError as e:
            last_exc = e
            msg = str(e.__cause__ or e)

            if "password authentication failed" in msg.lower():
                logger.error("Database authentication failed: %s", msg)
                raise

            logger.warning(
                "DB not ready (attempt %d/%d): %s",
                attempt, max_retries, msg
            )
            await asyncio.sleep(delay)

        except Exception as e:
            last_exc = e
            logger.exception(
                "Unexpected DB connection error (attempt %d/%d): %s",
                attempt, max_retries, e
            )
            await asyncio.sleep(delay)

    logger.error("Failed to connect to DB after %d retries. Last error: %s",
                 max_retries, last_exc)
    raise last_exc
