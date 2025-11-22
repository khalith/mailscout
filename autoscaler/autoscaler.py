import asyncio
import json
import os
import sys
import shlex
import subprocess
from datetime import datetime

import httpx
import redis.asyncio as redis

from config import settings


# ============================================================
#  Detect RUNTIME (local docker OR fly.io)
# ============================================================

def detect_runtime():
    if os.getenv("FLY_APP_NAME"):
        return "fly"
    return "docker"


RUNTIME = detect_runtime()
print(f"[autoscaler] Runtime detected => {RUNTIME}")


# ============================================================
#  Redis Queue Length
# ============================================================

async def get_queue_length(r):
    try:
        q = await r.llen(settings.QUEUE_KEY)
        print(f"[autoscaler] Checked Redis → queue length = {q}")
        return q
    except Exception as e:
        print(f"[autoscaler] Redis error while reading queue: {e}")
        return 0


# ============================================================
#  Docker Scaling (LOCAL)
# ============================================================

def _compose_cmd():
    cmd = ["docker", "compose"]
    if settings.COMPOSE_FILE:
        cmd += ["-f", settings.COMPOSE_FILE]
    if settings.COMPOSE_PROJECT:
        cmd += ["-p", settings.COMPOSE_PROJECT]
    return cmd


def docker_get_current_workers():
    try:
        out = subprocess.check_output(
            ["docker", "ps", "--format", "{{.Names}}"]
        ).decode()
        names = out.splitlines()
        count = sum("worker" in n for n in names)
        print(f"[autoscaler] Docker: detected {count} worker containers running")
        return count
    except Exception:
        print(f"[autoscaler] Docker: failed detecting workers, using MIN_WORKERS fallback")
        return settings.MIN_WORKERS


def docker_scale_workers(count):
    count = max(settings.MIN_WORKERS, min(settings.MAX_WORKERS, count))
    print(f"[autoscaler] Docker: scaling workers → target={count}")

    cmd = _compose_cmd() + ["up", "-d", "--scale", f"worker={count}"]

    try:
        subprocess.check_call(cmd)
        print(f"[autoscaler] Docker: scale request successful")
    except Exception as e:
        print(f"[autoscaler] Docker scale failed: {e}")


# ============================================================
#  Fly.io Machines API
# ============================================================

API = "https://api.machines.dev/v1"
FLY_TOKEN = os.getenv("FLY_API_TOKEN")
FLY_APP = os.getenv("FLY_APP_NAME")
FLY_REGION = os.getenv("FLY_REGION", "bom")

fly_headers = (
    {"Authorization": f"Bearer {FLY_TOKEN}", "Content-Type": "application/json"}
    if FLY_TOKEN
    else None
)


async def fly_list_workers():
    print("[autoscaler] Checking Fly.io worker machines...")

    if not fly_headers:
        print("[autoscaler] ERROR: Missing FLY_API_TOKEN")
        return []

    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                f"{API}/apps/{FLY_APP}/machines",
                headers=fly_headers,
                timeout=10,
            )
            r.raise_for_status()
            machines = r.json()
            workers = [m for m in machines if m["config"].get("metadata", {}).get("role") == "worker"]
            print(f"[autoscaler] Fly.io: found {len(workers)} worker machines")
            return workers
        except Exception as e:
            print("[autoscaler] Fly list error:", e)
            return []


async def fly_launch_worker():
    print("[autoscaler] Fly.io: launching new worker machine...")

    if not fly_headers:
        print("[autoscaler] Missing API token, cannot launch worker")
        return

    body = {
        "name": None,
        "region": FLY_REGION,
        "config": {
            "image": os.getenv("WORKER_IMAGE"),
            "metadata": {"role": "worker"},
            "restart": {"policy": "always"},
            "env": {
                "DATABASE_URL": os.getenv("DATABASE_URL"),
                "DATABASE_URL_SYNC": os.getenv("DATABASE_URL_SYNC"),
                "REDIS_URL": os.getenv("REDIS_URL"),
                "QUEUE_KEY": settings.QUEUE_KEY,
            },
        },
    }

    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                f"{API}/apps/{FLY_APP}/machines",
                headers=fly_headers,
                json=body,
            )
            r.raise_for_status()
            m = r.json()
            print(f"[autoscaler] Fly.io: Worker created → {m['id']}")
        except Exception as e:
            print("[autoscaler] Fly create error:", e)


async def fly_destroy_worker(machine_id):
    print(f"[autoscaler] Fly.io: destroying worker {machine_id} ...")

    async with httpx.AsyncClient() as client:
        try:
            r = await client.delete(
                f"{API}/apps/{FLY_APP}/machines/{machine_id}",
                headers=fly_headers,
                params={"force": "true"},
            )
            if r.status_code not in (200, 202):
                print("[autoscaler] destroy failed:", r.text)
            else:
                print("[autoscaler] Fly.io: destroyed worker", machine_id)
        except Exception as e:
            print("[autoscaler] destroy error:", e)


# ============================================================
#  AUTOSCALE LOOP
# ============================================================

async def autoscale_loop():
    r = redis.from_url(settings.REDIS_URL)
    idle_streak = 0

    print(
        f"[autoscaler] Autoscaler started at {datetime.utcnow().isoformat()} "
        f"(interval={settings.INTERVAL}s)"
    )

    while True:
        qlen = await get_queue_length(r)
        print(f"[autoscaler] --- Cycle Start --- Queue={qlen}")

        # ---------- Local Docker ----------
        if RUNTIME == "docker":
            current = docker_get_current_workers()

            if qlen > settings.SCALE_UP_THRESHOLD:
                print(f"[autoscaler] Queue high → considering scale up")
                if current < settings.MAX_WORKERS:
                    print(f"[autoscaler] Scaling up: {current} → {current + 1}")
                    docker_scale_workers(current + 1)
                else:
                    print("[autoscaler] Already at MAX_WORKERS, not scaling up")
                idle_streak = 0

            elif qlen == 0:
                idle_streak += 1
                print(f"[autoscaler] Queue empty → idle streak now {idle_streak}")
                if idle_streak >= settings.IDLE_CHECKS_BEFORE_SCALE_DOWN and current > settings.MIN_WORKERS:
                    print(f"[autoscaler] Scaling down: {current} → {current - 1}")
                    docker_scale_workers(current - 1)
                    idle_streak = 0
                else:
                    print("[autoscaler] Not scaling down yet")
            else:
                print("[autoscaler] Queue low but not empty → no scaling change")

        # ---------- Fly.io Machines ----------
        else:
            workers = await fly_list_workers()
            current = len(workers)

            if qlen > settings.SCALE_UP_THRESHOLD:
                print("[autoscaler] Queue high → considering scale up")
                if current < settings.MAX_WORKERS:
                    print(f"[autoscaler] Fly.io: scaling up → {current} → {current + 1}")
                    await fly_launch_worker()
                else:
                    print("[autoscaler] Fly.io: at MAX_WORKERS, cannot scale up")
                idle_streak = 0

            elif qlen == 0:
                idle_streak += 1
                print(f"[autoscaler] Queue empty → idle streak={idle_streak}")
                if idle_streak >= settings.IDLE_CHECKS_BEFORE_SCALE_DOWN and current > settings.MIN_WORKERS:
                    w = workers[-1]
                    print(f"[autoscaler] Fly.io: scaling down → removing {w['id']}")
                    await fly_destroy_worker(w["id"])
                    idle_streak = 0
                else:
                    print("[autoscaler] Fly.io: not scaling down yet")
            else:
                print("[autoscaler] Queue low → no scaling action")

        print(
            f"[autoscaler] Status → Queue={qlen}, Workers={current}, Idle={idle_streak}/{settings.IDLE_CHECKS_BEFORE_SCALE_DOWN}"
        )
        print("[autoscaler] --- Cycle End ---\n")

        await asyncio.sleep(settings.INTERVAL)


# ============================================================
#  ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    try:
        asyncio.run(autoscale_loop())
    except KeyboardInterrupt:
        sys.exit(0)
