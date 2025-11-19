# worker/worker.py
# Final, hardened worker implementation for MailScout.
# - Robust dynamic import of worker/verifier package
# - Handles sync & async verifier functions safely
# - Bounded concurrency for DNS/SMTP and overall email checks
# - Prevents coroutine/awaitable objects from being stored into JSON
# - Uses session.no_autoflush to avoid premature autoflush races
# - Clear, consistent logging and stable behavior in Docker

import asyncio
import json
import logging
import os
import sys
import inspect
from pathlib import Path
from typing import List, Optional, Tuple, Any, Dict

# Ensure /worker and backend app are importable
WORKER_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(WORKER_DIR, ".."))
if WORKER_DIR not in sys.path:
    sys.path.insert(0, WORKER_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Try to load the verifier package robustly
ms_verifier = None
try:
    # Prefer normal import if PYTHONPATH is set correctly
    import verifier as ms_verifier  # type: ignore
except Exception:
    try:
        verifier_init = Path(WORKER_DIR) / "verifier" / "__init__.py"
        if verifier_init.exists():
            import importlib.util

            spec = importlib.util.spec_from_file_location("verifier", str(verifier_init))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore
            ms_verifier = module
        else:
            ms_verifier = None
    except Exception:
        ms_verifier = None

# Third-party libs
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.config import settings
from app.models.upload import Upload, UploadStatus
from app.models.email_result import EmailResult

# Logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)
LOG = logging.getLogger("mailscout-worker")

# SQLAlchemy engine / session factory
engine = create_async_engine(settings.DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Concurrency configuration (tune via env)
WORKER_CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", "50"))
DNS_CONCURRENCY = int(os.getenv("DNS_CONCURRENCY", "50"))
SMTP_CONCURRENCY = int(os.getenv("SMTP_CONCURRENCY", "25"))

# Semaphores to bound concurrent tasks
_semaphore = asyncio.Semaphore(WORKER_CONCURRENCY)
_dns_semaphore = asyncio.Semaphore(DNS_CONCURRENCY)
_smtp_semaphore = asyncio.Semaphore(SMTP_CONCURRENCY)


# Helper to call verifier functions that might be sync or async.
# Returns None on errors; never returns coroutine objects.
async def _call_verifier(fn, *args, **kwargs):
    if fn is None:
        return None
    try:
        if inspect.iscoroutinefunction(fn):
            return await fn(*args, **kwargs)
        # If function is regular sync function, run in threadpool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))
    except Exception as e:
        LOG.debug("verifier function %s raised %s", getattr(fn, "__name__", str(fn)), e)
        return None


# Safe wrappers that call into ms_verifier when available.
# If ms_verifier is absent, they return sensible defaults.

async def normalize_email(email: str) -> str:
    if not ms_verifier:
        return (email or "").lower().strip()
    fn = getattr(ms_verifier, "normalize_email", None)
    out = await _call_verifier(fn, email)
    return (out or email or "").lower().strip()

async def is_syntax_valid(email: str) -> bool:
    if not ms_verifier:
        # basic fallback check: presence of '@' + a dot in domain
        return "@" in (email or "") and "." in (email.split("@")[-1] or "")
    fn = getattr(ms_verifier, "is_syntax_valid", None)
    out = await _call_verifier(fn, email)
    return bool(out)

async def is_disposable(email: str) -> bool:
    if not ms_verifier:
        return False
    fn = getattr(ms_verifier, "is_disposable", None)
    out = await _call_verifier(fn, email)
    return bool(out)

async def resolve_mx_for_domain(domain: str) -> List[str]:
    if not ms_verifier or not domain:
        return []
    fn = getattr(ms_verifier, "resolve_mx_for_domain", None)
    async with _dns_semaphore:
        out = await _call_verifier(fn, domain)
    if out is None:
        return []
    # ensure list of strings
    try:
        return [str(x) for x in out]
    except Exception:
        return []

async def smtp_check_rcpt(domain_or_mailbox: str) -> Optional[bool]:
    if not ms_verifier:
        return None
    fn = getattr(ms_verifier, "smtp_check_rcpt", None)
    async with _smtp_semaphore:
        return await _call_verifier(fn, domain_or_mailbox)

async def is_catch_all(domain: str) -> bool:
    if not ms_verifier or not domain:
        return False
    fn = getattr(ms_verifier, "is_catch_all", None)
    async with _dns_semaphore:
        out = await _call_verifier(fn, domain)
    return bool(out)

async def identify_provider(email: str) -> Optional[str]:
    if not ms_verifier:
        return None
    fn = getattr(ms_verifier, "identify_provider", None)
    return await _call_verifier(fn, email)

async def compute_score_and_status(email: Optional[str], checks: Dict[str, Any]) -> Tuple[int, str]:
    if not ms_verifier:
        # fallback simple scoring
        if not checks.get("syntax"):
            return 0, "invalid"
        if checks.get("has_mx"):
            return 90, "valid"
        return 30, "risky"
    fn = getattr(ms_verifier, "compute_score_and_status", None)
    out = await _call_verifier(fn, email, checks)
    if isinstance(out, (list, tuple)) and len(out) >= 2:
        try:
            return int(out[0] or 0), str(out[1] or "")
        except Exception:
            pass
    # final fallback
    return (0, "invalid") if not checks.get("syntax") else (90, "valid") if checks.get("has_mx") else (30, "risky")


# Sanitize object to make it JSON-serializable (remove awaitables/coroutines)
def _sanitize_for_json(obj):
    if inspect.isawaitable(obj) or inspect.iscoroutine(obj):
        return None
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(v) for v in obj]
    # basic scalar types are fine
    return obj


# Process single email with semaphore protection. Returns dict or None.
async def process_single_email(upload_id: str, email: str) -> Optional[dict]:
    async with _semaphore:
        try:
            normalized = await normalize_email(email)

            # syntax
            syntax_ok = await is_syntax_valid(normalized)

            domain = normalized.split("@")[-1] if "@" in normalized else ""
            mx_records = []
            if domain:
                mx_records = await resolve_mx_for_domain(domain) or []

            has_mx = bool(mx_records)

            disposable_flag = await is_disposable(normalized)
            catchall_flag = await is_catch_all(domain) if domain else False
            provider = await identify_provider(normalized)

            checks = {
                "syntax": syntax_ok,
                "domain": domain,
                "mx_records": mx_records,
                "has_mx": has_mx,
                "disposable": disposable_flag,
                "catch_all": catchall_flag,
                "provider": provider,
            }

            # compute score/status
            score, status = await compute_score_and_status(normalized, checks)

            # sanitize checks so no coroutine/awaitable objects leak
            checks = _sanitize_for_json(checks)

            return {
                "upload_id": upload_id,
                "email": normalized,
                "normalized": normalized,
                "status": status,
                "score": int(score or 0),
                "checks": checks,
            }
        except Exception:
            LOG.exception("Error processing email: %s", email)
            return None


# Process batch payload: run concurrent checks, write results with no_autoflush
async def process_payload(payload: dict, db: AsyncSession):
    upload_id = payload.get("upload_id")
    emails: List[str] = payload.get("emails") or []

    if not upload_id or not emails:
        LOG.warning("Invalid payload: %s", payload)
        return

    # load upload row
    q = await db.execute(select(Upload).where(Upload.id == upload_id))
    upload_obj = q.scalars().first()
    if not upload_obj:
        LOG.error("Upload not found: %s", upload_id)
        return

    # mark processing early and persist so UI sees it
    if upload_obj.status == UploadStatus.queued:
        upload_obj.status = UploadStatus.processing
        try:
            await db.commit()
        except Exception:
            # commit is best-effort; if it fails we'll continue
            await db.rollback()

    # spawn tasks for email checks (bounded concurrency happens inside process_single_email)
    tasks = [asyncio.create_task(process_single_email(upload_id, e)) for e in emails]
    results = []
    # collect as completed so we can start inserting earlier
    for coro in asyncio.as_completed(tasks):
        try:
            res = await coro
            if res:
                results.append(res)
        except Exception:
            LOG.exception("Unhandled exception in email task")

    if not results:
        # nothing to write; still ensure DB state persisted
        try:
            await db.commit()
        except Exception:
            await db.rollback()
        return

    inserted = 0
    # Avoid premature autoflush when we check for existing results
    with db.no_autoflush:
        for item in results:
            try:
                # double-check existence
                q2 = await db.execute(
                    select(EmailResult).where(
                        EmailResult.upload_id == upload_id,
                        EmailResult.email == item["email"],
                    )
                )
                if q2.scalars().first():
                    continue

                r = EmailResult(
                    upload_id=item["upload_id"],
                    email=item["email"],
                    normalized=item["normalized"],
                    status=item["status"],
                    score=item["score"],
                    checks=item["checks"],
                )
                db.add(r)
                inserted += 1
            except Exception:
                LOG.exception("Error inserting email result for %s", item.get("email"))

    # Update counters and status and commit
    try:
        upload_obj.processed_count = (upload_obj.processed_count or 0) + inserted
        if upload_obj.total_count and upload_obj.processed_count >= upload_obj.total_count:
            upload_obj.status = UploadStatus.completed
        await db.commit()
    except Exception:
        await db.rollback()
        LOG.exception("Failed to commit DB changes for upload=%s", upload_id)
        return

    LOG.info(
        "Processed payload for upload=%s inserted=%d processed_count=%d total=%d",
        upload_id,
        inserted,
        upload_obj.processed_count or 0,
        upload_obj.total_count or 0,
    )


# Main worker loop
async def worker_loop():
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    LOG.info("Worker connected to Redis: %s queue=%s", settings.REDIS_URL, settings.QUEUE_KEY)

    try:
        while True:
            try:
                res = await r.blpop(settings.QUEUE_KEY, timeout=5)
                if not res:
                    await asyncio.sleep(0.05)
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
                await asyncio.sleep(0.5)

    finally:
        try:
            await r.close()
        except Exception:
            pass
        try:
            await engine.dispose()
        except Exception:
            pass
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
