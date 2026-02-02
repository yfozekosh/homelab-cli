#!/bin/bash
set -e

echo "Starting Homelab Server..."

# Start FastAPI server in background
echo "Starting API server on port 8000..."
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait a bit for API to start
sleep 3

# Start Telegram bot if token is provided
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    echo "Starting Telegram bot..."
    python -m server.telegram_bot &
    BOT_PID=$!
else
    echo "TELEGRAM_BOT_TOKEN not set, skipping Telegram bot"
    BOT_PID=""
fi

# Function to handle shutdown
shutdown() {
    echo "Shutting down services..."
    if [ -n "$BOT_PID" ]; then
        kill $BOT_PID 2>/dev/null || true
    fi
    kill $API_PID 2>/dev/null || true
    wait
    echo "Shutdown complete"
    exit 0
}

trap shutdown SIGTERM SIGINT

# Wait for processes
echo "Homelab Server started successfully"
wait
