# backend/app/services/storage.py
import os
from pathlib import Path
from ..config import settings

UPLOAD_DIR = Path(settings.UPLOAD_PATH)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_upload_bytes(filename: str, data: bytes) -> str:
    path = UPLOAD_DIR / filename
    with open(path, "wb") as f:
        f.write(data)
    return str(path)
