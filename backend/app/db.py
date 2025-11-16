# backend/app/db.py
import logging
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

logger = logging.getLogger("mailscout.db")

# IMPORTANT — define Base here so Alembic can see metadata
Base = declarative_base()

# Create engine lazily (no immediate connect on import).
# Use settings.DATABASE_URL which is constructed from env in config.py
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=bool(settings.DEBUG),
    future=True,
)

# Session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# Helper: connection check with retries (can be called from startup scripts)
async def wait_for_db(max_retries: int = 8, delay: float = 2.0):
    """
    Attempt to connect to the DB a few times and surface a clearer diagnostic
    in case of authentication error vs network error.
    """
    from sqlalchemy.exc import OperationalError
    import sqlalchemy

    last_exc = None
    for i in range(max_retries):
        try:
            async with engine.connect() as conn:
                # quick lightweight ping
                await conn.execute(sqlalchemy.text("SELECT 1"))
                logger.info("Database connected (attempt %d)", i + 1)
                return True
        except OperationalError as e:
            # OperationalError from driver: likely auth or network
            last_exc = e
            msg = str(e.__cause__ or e)
            # Surface auth-specific message
            if "password authentication failed" in msg.lower():
                logger.error("Database authentication failed: %s", msg)
                raise
            logger.warning("DB not ready (attempt %d/%d): %s", i + 1, max_retries, msg)
            await asyncio.sleep(delay)
        except Exception as e:
            last_exc = e
            logger.exception("Unexpected error while waiting for DB: %s", e)
            await asyncio.sleep(delay)

    logger.error("Could not connect to database after %d retries: last error: %s", max_retries, last_exc)
    raise last_exc
