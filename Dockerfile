FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from repo
COPY flask_backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy application code and assets from repo root
COPY flask_backend /app/flask_backend
COPY web /app/web
COPY ml_models /app/ml_models
COPY data /app/data

ENV PYTHONPATH=/app

# PORT is injected by Render; default fallback for local
ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost:$PORT/health || exit 1

ENV WEB_WORKERS=1 WEB_THREADS=4

# WSGI entrypoint
CMD gunicorn -w ${WEB_WORKERS} --threads ${WEB_THREADS} -b 0.0.0.0:$PORT \
    --access-logfile - --error-logfile - flask_backend.wsgi:app
