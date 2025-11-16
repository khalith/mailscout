# backend/app/routers/results.py
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import io
import csv

from openpyxl import Workbook

from ..db import get_session
from ..models.email_result import EmailResult
from ..models.upload import Upload

router = APIRouter()


@router.get("/download/{upload_id}", response_model=None)
async def download_results(
    upload_id: str,
    file_format: str = Query("csv", regex="^(csv|xlsx|txt)$"),
    session: AsyncSession = Depends(get_session)
):
    # Validate upload exists and completed
    upload = await session.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    if upload.status != "completed":
        raise HTTPException(status_code=400, detail="Upload not yet completed")

    # Fetch results
    results = (
        await session.execute(
            select(EmailResult).where(EmailResult.upload_id == upload_id)
        )
    ).scalars().all()

    headers = ["email", "normalized", "status", "score", "checks", "created_at"]

    # -----------------------
    # CSV (UTF-8 with BOM)
    # -----------------------
    if file_format == "csv":
        text_buffer = io.StringIO()
        writer = csv.writer(text_buffer)
        writer.writerow(headers)

        for r in results:
            writer.writerow([r.email, r.normalized, r.status, r.score, r.checks, r.created_at])

        byte_buffer = io.BytesIO()
        byte_buffer.write("\ufeff".encode("utf-8"))  # BOM for Excel
        byte_buffer.write(text_buffer.getvalue().encode("utf-8"))
        byte_buffer.seek(0)

        return StreamingResponse(
            byte_buffer,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="results_{upload_id}.csv"'}
        )

    # -----------------------
    # TXT (tab separated)
    # -----------------------
    if file_format == "txt":
        text_buffer = io.StringIO()
        # write header as tab-separated for TXT too (optional)
        text_buffer.write("\t".join(headers) + "\n")
        for r in results:
            text_buffer.write(f"{r.email}\t{r.normalized}\t{r.status}\t{r.score}\t{r.checks}\t{r.created_at}\n")

        byte_buffer = io.BytesIO(text_buffer.getvalue().encode("utf-8"))
        byte_buffer.seek(0)

        return StreamingResponse(
            byte_buffer,
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="results_{upload_id}.txt"'}
        )

    # -----------------------
    # XLSX (real Excel file)
    # -----------------------
    if file_format == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.append(headers)

        for r in results:
            ws.append([r.email, r.normalized, r.status, r.score, r.checks, r.created_at])

        xlsx_buffer = io.BytesIO()
        wb.save(xlsx_buffer)
        xlsx_buffer.seek(0)

        return StreamingResponse(
            xlsx_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="results_{upload_id}.xlsx"'}
        )

    # Unsupported format (shouldn't reach due to regex)
    raise HTTPException(status_code=400, detail="Unsupported file format")
