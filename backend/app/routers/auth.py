# backend/app/routers/auth.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/ping")
async def ping():
    return {"msg": "auth placeholder"}
