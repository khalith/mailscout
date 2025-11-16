from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import uploads, results, auth

app = FastAPI(title=settings.APP_NAME)

# ---------------------------------------------------
# CORS (safe for local dev, restrict for production)
# ---------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*",  # DEV ONLY — remove for production / replace with explicit origins
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------
# Health check
# ---------------------------------------------------
@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}

# ---------------------------------------------------
# Routers
# ---------------------------------------------------
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
app.include_router(results.router, prefix="/results", tags=["results"])

# ---------------------------------------------------
# Note:
# Don't run uvicorn.run() inside the container — your Dockerfile / compose should
# start uvicorn as the container CMD/entrypoint.
# ---------------------------------------------------
