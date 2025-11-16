import enum
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.postgresql import ENUM
from app.db import Base


class UploadStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    cancelled = "cancelled"


# This matches EXACTLY the ENUM from migration
upload_status_enum = ENUM(
    UploadStatus,
    name="uploadstatus",
    create_type=False,    # Do NOT recreate in SQLAlchemy
    native_enum=True
)


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=True, index=True)
    filename = Column(String, nullable=False)
    total_count = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)

    # Use the real PostgreSQL ENUM
    status = Column(upload_status_enum, nullable=False, default=UploadStatus.queued)

    meta = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
