# autoscaler/autoscaler.py
import asyncio
import json
import subprocess
import shlex
import sys
from datetime import datetime

import redis.asyncio as redis

from config import settings

# --- Helpers --------------------------------------------------------------

async def get_queue_length(r):
    try:
        return await r.llen(settings.QUEUE_KEY)
    except Exception as e:
        print(f"[autoscaler] Redis error reading queue length: {e}")
        return 0

def _compose_cmd_base():
    base = ["docker", "compose"]
    if settings.COMPOSE_FILE:
        base += ["-f", settings.COMPOSE_FILE]
    if settings.COMPOSE_PROJECT:
        base += ["-p", settings.COMPOSE_PROJECT]
    return base

def get_current_workers():
    """
    Count running containers whose names indicate 'worker' replicas for this compose project.
    This is intentionally conservative — it looks for containers with 'worker' in the name.
    """
    try:
        cmd = ["docker", "ps", "--format", "{{.Names}}"]
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode().strip()
        names = out.splitlines()
        # conservative: count names containing "worker" substring
        cnt = sum(1 for n in names if "worker" in n)
        return max(cnt, settings.MIN_WORKERS)
    except Exception:
        return settings.MIN_WORKERS

def scale_workers(count):
    """
    Scale the worker service using docker-compose.
    """
    count = max(settings.MIN_WORKERS, min(settings.MAX_WORKERS, count))
    base = _compose_cmd_base()
    cmd = base + ["up", "-d", "--scale", f"worker={count}"]
    print(f"[autoscaler] Running: {' '.join(shlex.quote(p) for p in cmd)}")
    try:
        subprocess.check_call(cmd)
        print(f"[autoscaler] Scaled workers => {count}")
    except subprocess.CalledProcessError as e:
        print(f"[autoscaler] Scale command failed: {e}")

# --- Main loop ------------------------------------------------------------

async def autoscale_loop():
    r = redis.from_url(settings.REDIS_URL)
    idle_low_count = 0

    print(f"[autoscaler] started at {datetime.utcnow().isoformat()} checking every {settings.INTERVAL}s")
    try:
        while True:
            qlen = await get_queue_length(r)
            current = get_current_workers()

            print(f"[autoscaler] Queue={qlen}, Workers={current}, time={datetime.utcnow().isoformat()}")

            # --- SCALE UP ---
            # Check the aggressive rule FIRST
            if qlen > settings.SCALE_UP_THRESHOLD * 2 and current < settings.MAX_WORKERS:
                new_count = min(settings.MAX_WORKERS, current + 2)
                scale_workers(new_count)
                idle_low_count = 0

            # Normal scale-up
            elif qlen > settings.SCALE_UP_THRESHOLD and current < settings.MAX_WORKERS:
                new_count = min(settings.MAX_WORKERS, current + 1)
                scale_workers(new_count)
                idle_low_count = 0

            # --- SCALE DOWN ---
            elif qlen < settings.SCALE_DOWN_THRESHOLD:
                idle_low_count += 1
                print(
                    f"[autoscaler] idle low count = {idle_low_count}/{settings.IDLE_CHECKS_BEFORE_SCALE_DOWN}"
                )

                if (
                    idle_low_count >= settings.IDLE_CHECKS_BEFORE_SCALE_DOWN
                    and current > settings.MIN_WORKERS
                ):
                    new_count = max(settings.MIN_WORKERS, current - 1)
                    scale_workers(new_count)
                    idle_low_count = 0
            else:
                idle_low_count = 0

            await asyncio.sleep(settings.INTERVAL)
    finally:
        await r.close()

# --- Entrypoint -----------------------------------------------------------

if __name__ == "__main__":
    try:
        asyncio.run(autoscale_loop())
    except KeyboardInterrupt:
        print("[autoscaler] stopped by user")
        sys.exit(0)
