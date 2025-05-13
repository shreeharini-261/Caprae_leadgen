# Use Python 3.8 slim image
FROM python:3.8-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Create backend directory and copy files
RUN mkdir -p /app/backend
COPY backend/ /app/backend/

COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV FLASK_APP=backend/app.py
ENV FLASK_ENV=production
ENV GUNICORN_CMD_ARGS="--workers=4 --bind=0.0.0.0:8000 --timeout=120"
ENV PYTHONPATH=/app/backend

EXPOSE 8000

# Use the entrypoint script
ENTRYPOINT ["./entrypoint.sh"]