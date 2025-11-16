# backend/app/routers/results.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from ..models.email_result import EmailResult
from sqlalchemy import select

router = APIRouter()

@router.get("/{upload_id}")
async def get_results(upload_id: str, limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)):
    q = select(EmailResult).where(EmailResult.upload_id == upload_id).limit(limit).offset(offset)
    resp = await db.execute(q)
    items = resp.scalars().all()
    return {"count": len(items), "results": [ {
        "email": r.email, "status": r.status, "score": r.score, "checks": r.checks
    } for r in items]}
