# Ziggy Backend - Dockerfile (Poetry export -> pip install)
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps for scientific stack and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies from Poetry export
# Expect requirements.txt to be generated via `make freeze`
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

EXPOSE 8000

# Default command; override in docker-compose if needed
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
