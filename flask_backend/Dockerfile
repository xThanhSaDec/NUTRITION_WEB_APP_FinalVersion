FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (curl for healthcheck & simple fetches)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (context is already flask_backend/ on Render)
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy entire repo so app can access web/, ml_models/, data/
COPY . /app
ENV PYTHONPATH=/app

# Render injects $PORT; provide a fallback for local docker run
ENV PORT=8000
EXPOSE 8000

# Healthcheck uses dynamic $PORT so it works both locally and on Render
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost:$PORT/health || exit 1

# Configurable Gunicorn settings via env (with safe defaults for Free plan)
# WEB_WORKERS default 1, WEB_THREADS default 4
ENV WEB_WORKERS=1 WEB_THREADS=4

# Gunicorn loads app from wsgi module (no --factory for compatibility)
CMD gunicorn -w ${WEB_WORKERS} --threads ${WEB_THREADS} -b 0.0.0.0:$PORT flask_backend.wsgi:app
