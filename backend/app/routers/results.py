from fastapi import APIRouter, HTTPException, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import io
import csv

from ..db import get_session
from ..models.email_result import EmailResult
from ..models.upload import Upload

router = APIRouter()


@router.get("/download/{upload_id}", response_model=None)
async def download_results(
    upload_id: str,
    file_format: str = Query("csv", regex="^(csv|txt)$"),
    session: AsyncSession = Depends(get_session),
):
    # Validate upload exists
    upload = await session.get(Upload, upload_id)
    if not upload:
        raise HTTPException(404, "Upload not found")

    # --- FIX: Determine completion by counting results ---
    q = await session.execute(
        select(func.count()).select_from(EmailResult).where(EmailResult.upload_id == upload_id)
    )
    result_count = q.scalar_one() or 0

    if result_count < (upload.total_count or 0):
        raise HTTPException(400, "Upload not yet completed")

    # Fetch all results
    results = (
        await session.execute(
            select(EmailResult).where(EmailResult.upload_id == upload_id)
        )
    ).scalars().all()

    headers = ["email", "normalized", "status", "score", "checks", "created_at"]

    # CSV
    if file_format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(headers)
        for r in results:
            writer.writerow([
                r.email,
                r.normalized,
                r.status,
                r.score,
                r.checks,
                r.created_at,
            ])
        payload = ("\ufeff" + buf.getvalue()).encode("utf-8")
        return Response(
            payload,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename=\"results_{upload_id}.csv\"'}
        )

    # TXT
    if file_format == "txt":
        buf = io.StringIO()
        buf.write("\t".join(headers) + "\n")
        for r in results:
            buf.write(
                f"{r.email}\t{r.normalized}\t{r.status}\t{r.score}\t{r.checks}\t{r.created_at}\n"
            )
        payload = buf.getvalue().encode("utf-8")
        return Response(
            payload,
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename=\"results_{upload_id}.txt\"'}
        )

    raise HTTPException(400, "Unsupported file format")
