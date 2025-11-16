# worker/worker.py
import asyncio
import json
import logging
import os
import asyncpg
from typing import List

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update

# Import your app models/config. Adjust import path depending where you run this file.
# If this worker runs from root where `backend/app` is on PYTHONPATH, adjust accordingly.
from app.config import settings
from app.models.upload import Upload, UploadStatus
from app.models.email_result import EmailResult  # ensure this model exists and has upload_id,email,status,score,checks
from app.db import Base  # optional, for introspection

LOG = logging.getLogger("mailscout-worker")
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
                    format="%(asctime)s %(levelname)s %(message)s")


# create DB engine & session factory
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def process_payload(payload: dict, db: AsyncSession):
    """
    payload example: {"upload_id": "...", "emails": ["a@b.com", "c@d.com", ...]}
    This function inserts EmailResult rows (status unknown initially) and updates upload counters.
    """
    upload_id = payload.get("upload_id")
    emails: List[str] = payload.get("emails") or []
    if not upload_id or not emails:
        LOG.warning("Invalid payload: %s", payload)
        return

    # mark upload as processing if queued
    q = await db.execute(select(Upload).where(Upload.id == upload_id))
    upload_obj = q.scalars().first()
    if not upload_obj:
        LOG.error("Upload not found for id=%s", upload_id)
        return

    if upload_obj.status == UploadStatus.queued:
        upload_obj.status = UploadStatus.processing

    inserted = 0
    for email in emails:
        # idempotency: avoid duplicate results if reprocessing - simple check by upload_id+email
        q2 = await db.execute(
            select(EmailResult).where(
                EmailResult.upload_id == upload_id,
                EmailResult.email == email
            )
        )
        if q2.scalars().first():
            continue

        r = EmailResult(
            upload_id=upload_id,
            email=email,
            normalized=email.lower().strip(),
            status="pending",
            score=0,
            checks={},
        )
        db.add(r)
        inserted += 1

    # update processed_count
    upload_obj.processed_count = (upload_obj.processed_count or 0) + inserted

    # if processed_count >= total_count consider completed
    if upload_obj.total_count and upload_obj.processed_count >= upload_obj.total_count:
        upload_obj.status = UploadStatus.completed

    await db.commit()
    LOG.info("Processed payload for upload=%s inserted=%d processed_count=%d total=%d",
             upload_id, inserted, upload_obj.processed_count or 0, upload_obj.total_count or 0)


async def worker_loop():
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    LOG.info("Worker connected to Redis: %s queue=%s", settings.REDIS_URL, settings.QUEUE_KEY)

    try:
        while True:
            try:
                # BLPOP returns a tuple (key, value) or None
                res = await r.blpop(settings.QUEUE_KEY, timeout=5)
                if not res:
                    # nothing to do — short sleep then continue (keeps loop responsive)
                    await asyncio.sleep(0.1)
                    continue

                _, raw = res
                try:
                    payload = json.loads(raw)
                except Exception:
                    LOG.exception("Invalid JSON payload popped: %s", raw)
                    continue

                async with AsyncSessionLocal() as db:
                    await process_payload(payload, db)

            except Exception:
                LOG.exception("Unhandled error in worker iteration")
                # recover loop after short delay
                await asyncio.sleep(1.0)

    finally:
        await r.close()
        await engine.dispose()
        LOG.info("Worker shutdown")


def main():
    LOG.info("Starting mailscout worker")
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(worker_loop())
    except (KeyboardInterrupt, SystemExit):
        LOG.info("Worker received exit signal")
    finally:
        LOG.info("Worker done")


if __name__ == "__main__":
    main()
