# worker/utils/mx_limiter.py
import asyncio

# In-memory semaphore store
_mx_limits = {}
_lock = asyncio.Lock()

async def get_mx_semaphore(mx_host: str, limit: int):
    async with _lock:
        if mx_host not in _mx_limits:
            _mx_limits[mx_host] = asyncio.Semaphore(limit)
        return _mx_limits[mx_host]
