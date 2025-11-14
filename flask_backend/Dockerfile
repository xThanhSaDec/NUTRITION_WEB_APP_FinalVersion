FROM python:3.10-slim
WORKDIR /app
# system deps
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY flask_backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Copy full repo so we can import existing services and serve web
COPY . /app
ENV PYTHONPATH=/app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD curl -f http://localhost:8000/health || exit 1
CMD ["python", "-m", "flask_backend.app.flask_app"]
