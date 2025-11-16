import asyncio
import json
import subprocess
import redis.asyncio as redis

from config import settings


async def get_queue_length(r):
    """Return queue length safely."""
    try:
        return await r.llen(settings.QUEUE_KEY)
    except Exception:
        return 0


def get_current_workers():
    """
    Uses Fly.io CLI to fetch the current number of worker instances.
    """
    try:
        output = subprocess.check_output(
            ["fly", "scale", "show", "-j", "-a", settings.FLY_APP_NAME]
        )
        data = json.loads(output)
        return int(data["vm"]["count"])
    except Exception:
        return settings.MIN_WORKERS


def scale_workers(count):
    """
    Scale worker count using Fly CLI.
    """
    print(f"[autoscaler] Scaling workers to {count}")
    try:
        subprocess.call(
            ["fly", "scale", "count", str(count), "-a", settings.FLY_APP_NAME]
        )
    except Exception as e:
        print(f"[autoscaler] Scale failed: {e}")


async def autoscale_loop():
    """
    Main autoscaling loop: monitor queue length and scale up/down.
    """
    r = redis.from_url(settings.REDIS_URL)  # FIXED

    while True:
        qlen = await get_queue_length(r)
        current = get_current_workers()

        print(f"[autoscaler] Queue={qlen}, Workers={current}")

        # SCALE UP
        if qlen > settings.SCALE_UP_THRESHOLD and current < settings.MAX_WORKERS:
            new_count = min(settings.MAX_WORKERS, current + 1)
            scale_workers(new_count)

        # SCALE DOWN
        elif (
            qlen < settings.SCALE_DOWN_THRESHOLD
            and current > settings.MIN_WORKERS
        ):
            new_count = max(settings.MIN_WORKERS, current - 1)
            scale_workers(new_count)

        await asyncio.sleep(settings.INTERVAL)


if __name__ == "__main__":
    try:
        asyncio.run(autoscale_loop())
    except KeyboardInterrupt:
        print("Autoscaler stopped.")
