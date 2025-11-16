FROM python:3.10-slim
WORKDIR /app
# System deps (curl for healthcheck & simple fetches)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements (relative path assumes build context is repo root on Render)
COPY flask_backend/requirements.txt ./requirements.txt
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

# Lightweight Gunicorn settings for Render Free (1 worker, 4 threads)
# Use factory syntax to call create_app()
CMD gunicorn --factory -w 1 --threads 4 -b 0.0.0.0:$PORT flask_backend.app.flask_app:create_app
