# worker/utils/mx_limiter.py
import asyncio
from typing import Dict

class MXLimiter:
    """
    Simple per-domain concurrency limiter + cache for MX lookups.
    Prevents repetitive DNS MX queries for the same domain in a short time.
    """
    def __init__(self, max_concurrent: int = 6, ttl_seconds: int = 300):
        self._sem = asyncio.Semaphore(max_concurrent)
        self._cache: Dict[str, dict] = {}
        self._ttl = ttl_seconds

    async def get_or_set(self, domain: str, coro):
        # Return cached if fresh
        entry = self._cache.get(domain)
        if entry:
            if entry["expiry"] >= asyncio.get_event_loop().time():
                return entry["value"]
            else:
                del self._cache[domain]

        async with self._sem:
            value = await coro(domain)
            self._cache[domain] = {
                "value": value,
                "expiry": asyncio.get_event_loop().time() + self._ttl,
            }
            return value
