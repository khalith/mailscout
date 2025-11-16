# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "mailscout"
    # Redis & queue
    REDIS_URL: str = "redis://redis:6379/0"
    QUEUE_KEY: str = "mailscout_jobs"   # single authoritative queue key
    # DB
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/mailscout"
    # chunking
    CHUNK_SIZE: int = 1000
    # other useful defaults
    LOG_LEVEL: str = "INFO"

    # Auth / JWT
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # File upload limits
    MAX_UPLOAD_SIZE_MB: int = 256
    
    DEBUG: bool = False  # <-- REQUIRED

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
