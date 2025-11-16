import asyncio
from alembic import command
from alembic.config import Config
import os

async def run_migrations():
    # Path to alembic.ini inside the container
    config_path = os.path.join(os.path.dirname(__file__), "../alembic.ini")
    alembic_cfg = Config(config_path)

    # Run migrations
    command.upgrade(alembic_cfg, "head")

if __name__ == "__main__":
    asyncio.run(run_migrations())
