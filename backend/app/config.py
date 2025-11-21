# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    APP_NAME: str = "mailscout"

    POSTGRES_USER: str = os.environ.get("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.environ.get("POSTGRES_DB", "mailscout")
    POSTGRES_HOST: str = os.environ.get("POSTGRES_HOST", "db")
    POSTGRES_PORT: str = os.environ.get("POSTGRES_PORT", "5432")

    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    # Redis & queue
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://redis:6379/0")

    QUEUE_KEY: str = "mailscout:jobs"

    # chunking
    CHUNK_SIZE: int = int(os.environ.get("CHUNK_SIZE", 1000))
    # other useful defaults
    LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")

    # Auth / JWT
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "change-me")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))

    # File upload limits
    MAX_UPLOAD_SIZE_MB: int = int(os.environ.get("MAX_UPLOAD_SIZE_MB", 256))

    DEBUG: bool = os.environ.get("DEBUG", "False").lower() in ("1", "true", "yes")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
