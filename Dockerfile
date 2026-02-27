# Minimal Dockerfile for hosting PTA EMR Playground
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for psycopg2 (optional if you use psycopg2-binary)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Cloud platforms usually inject PORT; default to 5000 locally
ENV PORT=5000

# Use gunicorn in production
CMD gunicorn wsgi:app --bind 0.0.0.0:$PORT
