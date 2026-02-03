#!/bin/bash
set -e

echo "Starting Homelab Server..."

# Setup SSH directory with correct permissions
if [ -d "/host-ssh" ]; then
    echo "Setting up SSH keys..."
    mkdir -p /root/.ssh
    chmod 700 /root/.ssh
    
    # Copy SSH keys
    if [ -f "/host-ssh/id_rsa" ]; then
        cp /host-ssh/id_rsa /root/.ssh/
        chmod 600 /root/.ssh/id_rsa
        echo "  ✓ Copied id_rsa"
    fi
    
    if [ -f "/host-ssh/id_ed25519" ]; then
        cp /host-ssh/id_ed25519 /root/.ssh/
        chmod 600 /root/.ssh/id_ed25519
        echo "  ✓ Copied id_ed25519"
    fi
    
    if [ -f "/host-ssh/id_ecdsa" ]; then
        cp /host-ssh/id_ecdsa /root/.ssh/
        chmod 600 /root/.ssh/id_ecdsa
        echo "  ✓ Copied id_ecdsa"
    fi
    
    # Copy known_hosts if exists
    if [ -f "/host-ssh/known_hosts" ]; then
        cp /host-ssh/known_hosts /root/.ssh/
        chmod 600 /root/.ssh/known_hosts
        echo "  ✓ Copied known_hosts"
    fi
    
    # Copy user config if exists, with strict permissions
    if [ -f "/host-ssh/config" ]; then
        cp /host-ssh/config /root/.ssh/config
        chmod 600 /root/.ssh/config
        echo "  ✓ Copied user config"
    fi
    
    # Create/append SSH config to disable host key checking
    # This prevents "Are you sure you want to continue connecting?" prompts
    cat >> /root/.ssh/config << 'EOF'

# Homelab automation settings
Host *
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
EOF
    chmod 600 /root/.ssh/config
    echo "  ✓ Configured SSH to skip host verification"
    
    echo "SSH setup complete"
else
    echo "⚠️  No SSH directory mounted at /host-ssh"
    echo "   SSH functionality will not work"
fi

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
