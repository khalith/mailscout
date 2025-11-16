# run_migrations.py (wraps alembic call with wait_for_db)
import asyncio
import logging
from alembic import command
from alembic.config import Config
from app.db import wait_for_db
from app.config import settings

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("run_migrations")

async def run_migrations():
    # wait for DB (will raise if auth fails)
    await wait_for_db(max_retries=8, delay=2.0)

    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")

if __name__ == "__main__":
    asyncio.run(run_migrations())
