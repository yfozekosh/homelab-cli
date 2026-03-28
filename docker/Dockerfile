FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    iputils-ping \
    dnsutils \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server/ ./server/

# Create data directory for persistent config
RUN mkdir -p /app/data

# Expose API port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CONFIG_PATH=/app/data/config.json

# Health check - verifies both API and bot health
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "\
import requests, sys; \
r = requests.get('http://localhost:8000/health', timeout=5); \
b = requests.get('http://localhost:8000/bot/health', timeout=5); \
bd = b.json(); \
sys.exit(0 if r.json().get('status') == 'healthy' and bd.get('status') in ['healthy', 'unknown'] else 1)"

# Start script that runs both API server and Telegram bot
COPY docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
