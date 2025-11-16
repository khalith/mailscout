# backend/app/models/email_result.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.db import Base

class EmailResult(Base):
    __tablename__ = "email_results"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(String, ForeignKey("uploads.id", ondelete="CASCADE"), index=True, nullable=False)
    email = Column(String, index=True, nullable=False)
    normalized = Column(String, index=True)
    status = Column(String, nullable=True)
    score = Column(Integer, default=0)
    checks = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
