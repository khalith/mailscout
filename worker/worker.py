# worker/worker.py

import asyncio
import json
import logging
import re
import dns.resolver
import asyncpg
import redis.asyncio as redis
from typing import List

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.config import settings
from app.models.upload import Upload, UploadStatus
from app.models.email_result import EmailResult

# ---------------------------------------------------------
# logging — FIXED (your old version was corrupted)
# ---------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)

LOG = logging.getLogger("mailscout-worker")

# ---------------------------------------------------------
# SQLAlchemy engine
# ---------------------------------------------------------
engine = create_async_engine(settings.DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# ---------------------------------------------------------
# Email syntax check
# ---------------------------------------------------------
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def is_syntax_valid(email: str) -> bool:
    return EMAIL_REGEX.match(email) is not None

# ---------------------------------------------------------
# MX lookup
# ---------------------------------------------------------
def check_mx(domain: str):
    try:
        answers = dns.resolver.resolve(domain, "MX")
        mx_hosts = sorted([str(r.exchange).rstrip('.') for r in answers])
        return mx_hosts
    except Exception:
        return []

# ---------------------------------------------------------
# Score logic
# ---------------------------------------------------------
def compute_score(is_valid, has_mx):
    if not is_valid:
        return 0
    if is_valid and not has_mx:
        return 30
    if is_valid and has_mx:
        return 90
    return 0

# ---------------------------------------------------------
# Status mapping
# ---------------------------------------------------------
def compute_status(is_valid, has_mx):
    if not is_valid:
        return "invalid"
    if is_valid and not has_mx:
        return "risky"
    return "valid"

# ---------------------------------------------------------
# Process payload batch
# ---------------------------------------------------------
async def process_payload(payload: dict, db: AsyncSession):
    upload_id = payload.get("upload_id")
    emails: List[str] = payload.get("emails") or []

    if not upload_id or not emails:
        LOG.warning("Invalid payload: %s", payload)
        return

    # Load upload object
    q = await db.execute(select(Upload).where(Upload.id == upload_id))
    upload_obj = q.scalars().first()
    if not upload_obj:
        LOG.error("Upload not found: %s", upload_id)
        return

    # Set upload to processing
    if upload_obj.status == UploadStatus.queued:
        upload_obj.status = UploadStatus.processing

    inserted = 0

    for email in emails:
        normalized = email.lower().strip()

        # Skip duplicates
        q2 = await db.execute(
            select(EmailResult).where(
                EmailResult.upload_id == upload_id,
                EmailResult.email == normalized,
            )
        )
        if q2.scalars().first():
            continue

        # 1. Syntax check
        is_valid = is_syntax_valid(normalized)

        # 2. MX lookup
        domain = normalized.split("@")[-1]
        mx_records = check_mx(domain)
        has_mx = len(mx_records) > 0

        # 3. Score + status
        score = compute_score(is_valid, has_mx)
        status = compute_status(is_valid, has_mx)

        # 4. Save checks JSON
        checks = {
            "syntax": is_valid,
            "domain": domain,
            "mx_records": mx_records,
            "has_mx": has_mx,
        }

        # Insert result
        r = EmailResult(
            upload_id=upload_id,
            email=normalized,
            normalized=normalized,
            status=status,
            score=score,
            checks=checks,
        )
        db.add(r)
        inserted += 1

    # Update progress
    upload_obj.processed_count = (upload_obj.processed_count or 0) + inserted

    if upload_obj.total_count and upload_obj.processed_count >= upload_obj.total_count:
        upload_obj.status = UploadStatus.completed

    await db.commit()

    LOG.info(
        "Processed payload for upload=%s inserted=%d processed=%d total=%d",
        upload_id,
        inserted,
        upload_obj.processed_count,
        upload_obj.total_count,
    )


# ---------------------------------------------------------
# Worker loop
# ---------------------------------------------------------
async def worker_loop():
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    LOG.info("Worker connected to Redis: %s", settings.REDIS_URL)

    try:
        while True:
            try:
                res = await r.blpop(settings.QUEUE_KEY, timeout=5)
                if not res:
                    await asyncio.sleep(0.1)
                    continue

                _, raw = res
                payload = json.loads(raw)

                async with AsyncSessionLocal() as db:
                    await process_payload(payload, db)

            except Exception:
                LOG.exception("Error in worker loop")
                await asyncio.sleep(1)

    finally:
        await r.close()
        await engine.dispose()
        LOG.info("Worker shutdown")


def main():
    LOG.info("Starting mailscout worker")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(worker_loop())


if __name__ == "__main__":
    main()
