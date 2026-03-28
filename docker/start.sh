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
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 2>&1 &
API_PID=$!
echo "API server PID: $API_PID"

# Wait a bit for API to start
sleep 3

# Start Telegram bot if token is provided
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    echo "Starting Telegram bot..."
    (
        attempt=0
        max_delay=60
        watchdog_timeout=180  # Kill bot if no activity for 3 minutes
        
        while true; do
            attempt=$((attempt + 1))
            # Exponential backoff: 5s, 10s, 20s, 40s, 60s, 60s...
            delay=$((5 * (2 ** (attempt - 1))))
            if [ $delay -gt $max_delay ]; then
                delay=$max_delay
            fi
            
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot starting (attempt #${attempt})..."
            start_time=$(date +%s)
            
            # Start bot in background so we can monitor it
            python -m server.telegram_bot &
            BOT_INNER_PID=$!
            
            # Watchdog loop - monitor bot process
            while kill -0 $BOT_INNER_PID 2>/dev/null; do
                current_time=$(date +%s)
                elapsed=$((current_time - start_time))
                
                # Check if bot process is still alive
                if ! kill -0 $BOT_INNER_PID 2>/dev/null; then
                    break
                fi
                
                # Watchdog: kill if no progress for too long (check logs for activity)
                # For now, just monitor if process exists - more sophisticated checks
                # would parse logs for "polling started" or similar
                sleep 10
            done
            
            exit_code=$?
            
            end_time=$(date +%s)
            runtime=$((end_time - start_time))
            
            # If bot ran for more than 5 minutes, reset attempt counter (stable run)
            if [ $runtime -gt 300 ]; then
                attempt=0
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot was stable (ran ${runtime}s), resetting backoff"
            fi
            
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot exited with code ${exit_code} after ${runtime}s, restarting in ${delay}s..."
            sleep $delay
        done
    ) &
    BOT_PID=$!
    echo "Bot supervisor PID: $BOT_PID"
else
    echo "TELEGRAM_BOT_TOKEN not set, skipping Telegram bot"
    BOT_PID=""
fi

# Function to handle shutdown
shutdown() {
    echo "Shutting down services..."
    if [ -n "$BOT_PID" ]; then
        kill -- -$BOT_PID 2>/dev/null || kill $BOT_PID 2>/dev/null || true
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
