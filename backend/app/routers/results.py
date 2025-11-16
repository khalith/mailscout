from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import io
import csv

from ..db import get_session
from ..models.email_result import EmailResult
from ..models.upload import Upload

router = APIRouter()

@router.get("/download/{upload_id}", response_model=None)
async def download_results(
    upload_id: str,
    session: AsyncSession = Depends(get_session)   # ✔ FIXED
):
    # Check upload exists & completed
    upload = await session.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    if upload.status != "completed":
        raise HTTPException(status_code=400, detail="Upload not yet completed")

    # Fetch all results
    results = (
        await session.execute(
            select(EmailResult).where(EmailResult.upload_id == upload_id)
        )
    ).scalars().all()

    # Generate CSV in memory
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["email", "normalized", "status", "score", "checks", "created_at"])

    for r in results:
        writer.writerow([r.email, r.normalized, r.status, r.score, r.checks, r.created_at])

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=results_{upload_id}.csv"}
    )
