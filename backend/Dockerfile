# ============================
#   Stage 1 — Builder
# ============================
FROM python:3.11-slim AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.7.1
RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock* /app/

# Install dependencies (no dev)
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# ============================
#   Stage 2 — Final Runtime
# ============================
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local /usr/local

# Copy backend source
COPY app /app/app
COPY alembic /app/alembic
COPY alembic/alembic.ini /app/alembic.ini
COPY app/run_migrations.py /app/run_migrations.py

ENV PYTHONPATH="/app"
EXPOSE 8000

# Auto-run migrations, then start API
CMD ["bash", "-c", "python app/run_migrations.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
