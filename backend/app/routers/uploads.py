##backend/app/routers/uploads.py
import uuid
import csv
import io
import json
import openpyxl
import xlrd   # for .xls files

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..config import settings
from ..db import get_db
from ..models.upload import Upload, UploadStatus
import redis.asyncio as redis
from ..services.chunker import chunk_list
from fastapi import Path
from sqlalchemy import select, func
from ..models.email_result import EmailResult


router = APIRouter()


# ---------------------------------------------------
# Redis Pusher
# ---------------------------------------------------
async def push_jobs_to_redis(payloads):
    r = redis.from_url(settings.REDIS_URL)
    for p in payloads:
        await r.rpush(settings.QUEUE_KEY, json.dumps(p))
    await r.close()


# ---------------------------------------------------
# CSV/TXT Parser
# ---------------------------------------------------
def parse_csv(content: bytes):
    text = content.decode("utf-8", errors="ignore")
    reader = csv.reader(io.StringIO(text))

    emails = []
    for row in reader:
        if not row:
            continue
        cell = next((c.strip() for c in row if c.strip()), None)
        if cell:
            emails.append(cell)

    return emails


# ---------------------------------------------------
# XLSX Parser
# ---------------------------------------------------
def parse_xlsx(content: bytes):
    workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
    sheet = workbook.active

    emails = []
    for row in sheet.iter_rows(values_only=True):
        if not row:
            continue
        cell = next((str(c).strip() for c in row if c), None)
        if cell:
            emails.append(cell)

    return emails


# ---------------------------------------------------
# XLS Parser (old Excel format)
# ---------------------------------------------------
def parse_xls(content: bytes):
    workbook = xlrd.open_workbook(file_contents=content)
    sheet = workbook.sheet_by_index(0)

    emails = []
    for row_idx in range(sheet.nrows):
        row = sheet.row(row_idx)
        cleaned = [str(cell.value).strip() for cell in row if cell.value]
        if cleaned:
            emails.append(cleaned[0])

    return emails


# ---------------------------------------------------
# Upload Route
# ---------------------------------------------------
@router.post("/create")
async def create_upload(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    fname = file.filename.lower()

    # Allowed formats
    if not fname.endswith((".csv", ".txt", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only CSV, TXT, XLSX, XLS allowed")

    content = await file.read()

    # --- XLSX ---
    if fname.endswith(".xlsx"):
        emails = parse_xlsx(content)

    # --- XLS ---
    elif fname.endswith(".xls"):
        emails = parse_xls(content)

    # --- CSV or TXT ---
    else:
        emails = parse_csv(content)

    # Normalize + dedupe
    normalized = list(dict.fromkeys([e.lower().strip() for e in emails if "@" in e]))

    upload_id = str(uuid.uuid4())
    upload = Upload(
        id=upload_id,
        filename=file.filename,
        total_count=len(normalized),
        status=UploadStatus.queued,
    )

    db.add(upload)
    await db.commit()

    chunk_size = settings.CHUNK_SIZE
    payloads = [
        {"upload_id": upload_id, "emails": chunk}
        for chunk in chunk_list(normalized, chunk_size)
    ]

    background_tasks.add_task(push_jobs_to_redis, payloads)

    return JSONResponse(
        {
            "upload_id": upload_id,
            "total": len(normalized),
            "chunks": len(payloads),
        }
    )

@router.get("/{upload_id}")
async def get_upload_status(upload_id: str = Path(...), db: AsyncSession = Depends(get_db)):
    # get upload row
    q = await db.execute(select(Upload).where(Upload.id == upload_id))
    upload = q.scalars().first()
    if not upload:
        raise HTTPException(status_code=404, detail="upload not found")

    # count results inserted so far for this upload
    q2 = await db.execute(select(func.count()).select_from(EmailResult).where(EmailResult.upload_id == upload_id))
    inserted_count = q2.scalar_one() or 0

    # Optionally compute chunks (if total_count and CHUNK_SIZE available)
    chunk_size = settings.CHUNK_SIZE
    chunks = (upload.total_count + chunk_size - 1) // chunk_size if upload.total_count else 0

    return {
        "upload_id": upload.id,
        "status": str(upload.status),
        "processed": int(inserted_count),
        "total": int(upload.total_count or 0),
        "chunks": int(chunks),
    }
