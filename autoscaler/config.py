# autoscaler/config.py
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ---------------------------------------------------------
    # Redis queue
    # ---------------------------------------------------------
    REDIS_URL: str = os.getenv("REDIS_URL")
    QUEUE_KEY: str = "mailscout:jobs"

    # ---------------------------------------------------------
    # Scaling thresholds
    # ---------------------------------------------------------
    MIN_WORKERS: int = int(os.getenv("MIN_WORKERS", 1))
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", 5))

    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 10))
    SCALE_DOWN_THRESHOLD: int = int(os.getenv("SCALE_DOWN_THRESHOLD", 0))

    INTERVAL: int = int(os.getenv("INTERVAL", 15))  # seconds
    IDLE_CHECKS_BEFORE_SCALE_DOWN: int = int(os.getenv("IDLE_CHECKS_BEFORE_SCALE_DOWN", 3))

    # ---------------------------------------------------------
    # Docker compose local mode
    # ---------------------------------------------------------
    COMPOSE_FILE: str = os.getenv("COMPOSE_FILE", "docker-compose.yml")
    COMPOSE_PROJECT: str = os.getenv("COMPOSE_PROJECT", "mailscout")

    # ---------------------------------------------------------
    # Fly.io Machines
    # ---------------------------------------------------------
    FLY_API_TOKEN: str = os.getenv("FLY_API_TOKEN", "")
    FLY_REGION: str = os.getenv("FLY_REGION", "bom")
    WORKER_IMAGE: str = os.getenv("WORKER_IMAGE", "")  # must be set when scaling on Fly


settings = Settings()
