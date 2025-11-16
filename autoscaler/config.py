import os


class Settings:
    # Redis
    REDIS_URL = os.getenv("REDIS_URL")
    QUEUE_KEY = os.getenv("QUEUE_KEY", "mailscout:jobs")

    # Scaling thresholds
    SCALE_UP_THRESHOLD = int(os.getenv("SCALE_UP_THRESHOLD", "2000"))
    SCALE_DOWN_THRESHOLD = int(os.getenv("SCALE_DOWN_THRESHOLD", "200"))

    # Fly.io worker app
    FLY_APP_NAME = os.getenv("FLY_WORKER_APP", "mailscout-worker")

    # Worker pool limits
    MIN_WORKERS = int(os.getenv("MIN_WORKERS", "1"))
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "20"))

    # Check interval (seconds)
    INTERVAL = int(os.getenv("INTERVAL", "20"))


settings = Settings()
