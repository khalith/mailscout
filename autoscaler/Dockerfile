FROM python:3.11-slim

WORKDIR /autoscaler

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl bash && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy autoscaler source
COPY . .

CMD ["python", "autoscaler.py"]
