# backend/app/routers/uploads.py
import uuid
import csv
import io
import json
import openpyxl
import xlrd

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    HTTPException,
    Path,
)
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

import redis.asyncio as redis

from ..config import settings
from ..db import get_db
from ..models.upload import Upload, UploadStatus
from ..models.email_result import EmailResult
from ..services.chunker import chunk_list


router = APIRouter()


# ---------------------------------------------------
# Redis Pusher (SAFE, SYNC EXECUTION)
# ---------------------------------------------------
async def push_jobs_to_redis(payloads):
    r = redis.from_url(settings.REDIS_URL)
    for p in payloads:
        await r.rpush(settings.QUEUE_KEY, json.dumps(p))
    await r.close()


# ---------------------------------------------------
# CSV Parser
# ---------------------------------------------------
def parse_csv(content: bytes):
    text = content.decode("utf-8", errors="ignore")
    reader = csv.reader(io.StringIO(text))
    emails = []
    for row in reader:
        if row:
            c = next((v.strip() for v in row if v.strip()), None)
            if c:
                emails.append(c)
    return emails


# ---------------------------------------------------
# XLSX Parser
# ---------------------------------------------------
def parse_xlsx(content: bytes):
    workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
    sheet = workbook.active
    emails = []
    for row in sheet.iter_rows(values_only=True):
        if row:
            c = next((str(v).strip() for v in row if v), None)
            if c:
                emails.append(c)
    return emails


# ---------------------------------------------------
# XLS Parser
# ---------------------------------------------------
def parse_xls(content: bytes):
    workbook = xlrd.open_workbook(file_contents=content)
    sheet = workbook.sheet_by_index(0)
    emails = []
    for i in range(sheet.nrows):
        row = sheet.row(i)
        cleaned = [str(cell.value).strip() for cell in row if cell.value]
        if cleaned:
            emails.append(cleaned[0])
    return emails


# ---------------------------------------------------
# FIXED UPLOAD ROUTE (NO BACKGROUNDTASKS)
# ---------------------------------------------------
@router.post("/create")
async def create_upload(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):

    fname = file.filename.lower()
    if not fname.endswith((".csv", ".txt", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only CSV, TXT, XLSX, XLS allowed")

    content = await file.read()

    # Select parser
    if fname.endswith(".xlsx"):
        emails = parse_xlsx(content)
    elif fname.endswith(".xls"):
        emails = parse_xls(content)
    else:
        emails = parse_csv(content)

    # Normalize + dedupe
    normalized = list(dict.fromkeys([e.lower().strip() for e in emails if "@" in e]))

    upload_id = str(uuid.uuid4())

    # Save upload row
    upload = Upload(
        id=upload_id,
        filename=file.filename,
        total_count=len(normalized),
        status=UploadStatus.queued,
    )
    db.add(upload)
    await db.commit()

    # Chunk email list
    chunk_size = settings.CHUNK_SIZE
    payloads = [
        {"upload_id": upload_id, "emails": chunk}
        for chunk in chunk_list(normalized, chunk_size)
    ]

    # 🚀 IMPORTANT FIX: push synchronously (BackgroundTasks is unreliable inside Docker)
    await push_jobs_to_redis(payloads)

    return {
        "upload_id": upload_id,
        "total": len(normalized),
        "chunks": len(payloads),
    }


# ---------------------------------------------------
# Status Route
# ---------------------------------------------------
@router.get("/{upload_id}")
async def get_upload_status(
    upload_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(select(Upload).where(Upload.id == upload_id))
    upload = q.scalars().first()

    if not upload:
        raise HTTPException(status_code=404, detail="upload not found")

    q2 = await db.execute(
        select(func.count()).select_from(EmailResult).where(EmailResult.upload_id == upload_id)
    )
    inserted = q2.scalar_one() or 0

    chunk_size = settings.CHUNK_SIZE
    chunks = (upload.total_count + chunk_size - 1) // chunk_size if upload.total_count else 0

    return {
        "upload_id": upload.id,
        "status": str(upload.status),
        "processed": int(inserted),
        "total": int(upload.total_count or 0),
        "chunks": int(chunks),
    }
