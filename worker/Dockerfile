FROM python:3.11-slim

# System deps for asyncpg / psycopg compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /worker

# Install Python dependencies
COPY backend /tmp/backend/
RUN pip install --no-cache-dir /tmp/backend

COPY worker/requirements.txt /tmp/worker.txt
RUN pip install --no-cache-dir -r /tmp/worker.txt

# Copy backend shared code so worker can import app.config, app.models, etc.
COPY backend/app /app/app

# Copy worker code
COPY worker/worker.py /worker/worker.py
COPY worker/verifier /worker/verifier
COPY worker/utils /worker/utils

# Make backend and worker modules importable
ENV PYTHONPATH="/app:/worker"

# Run worker with unbuffered output so logs appear instantly
CMD ["python", "-u", "/worker/worker.py"]
