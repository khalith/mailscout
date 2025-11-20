# autoscaler/config.py
import os

class Settings:
    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    QUEUE_KEY = os.getenv("QUEUE_KEY", "mailscout:jobs")

    # Scaling thresholds
    SCALE_UP_THRESHOLD = int(os.getenv("SCALE_UP_THRESHOLD", "2000"))
    SCALE_DOWN_THRESHOLD = int(os.getenv("SCALE_DOWN_THRESHOLD", "200"))
    # Number of consecutive low-checks required before scaling down
    IDLE_CHECKS_BEFORE_SCALE_DOWN = int(os.getenv("IDLE_CHECKS_BEFORE_SCALE_DOWN", "3"))

    # Limits
    MIN_WORKERS = int(os.getenv("MIN_WORKERS", "1"))
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "20"))

    # Check interval (seconds)
    INTERVAL = int(os.getenv("INTERVAL", "10"))

    # Path to docker-compose file (optional)
    COMPOSE_FILE = os.getenv("COMPOSE_FILE", "docker-compose.yml")
    COMPOSE_PROJECT = os.getenv("COMPOSE_PROJECT", None)  # optional

settings = Settings()
