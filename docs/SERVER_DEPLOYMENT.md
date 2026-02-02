# Server Deployment Guide

This guide covers deploying the Homelab server using Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+
- A machine that can reach your LAN devices (smart plugs, servers)

## Installation Steps

### 1. Prepare the Environment

```bash
# Clone the repository
git clone <repository-url>
cd homelab-cli/docker

# Create environment file
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` file:

```bash
# Required: Tapo smart plug credentials
TAPO_USERNAME=your_tapo_email@example.com
TAPO_PASSWORD=your_tapo_password

# Required: API key for CLI authentication
API_KEY=generate-a-secure-random-key-here

# Optional: Telegram bot configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_USER_IDS=123456789,987654321
```

**Important Notes:**
- `TAPO_USERNAME` and `TAPO_PASSWORD`: Your Tapo app login credentials
- `API_KEY`: Generate a secure random string (min 32 characters recommended)
- `TELEGRAM_BOT_TOKEN`: Get from [@BotFather](https://t.me/botfather)
- `TELEGRAM_USER_IDS`: Get your ID from [@userinfobot](https://t.me/userinfobot)

### 3. Generate Secure API Key

```bash
# Linux/macOS
openssl rand -hex 32

# Or use Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Create Telegram Bot (Optional)

If you want Telegram integration:

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow instructions to create bot
4. Copy the bot token to `.env` file
5. Get your user ID from [@userinfobot](https://t.me/userinfobot)
6. Add your user ID to `TELEGRAM_USER_IDS` in `.env`

### 5. Build and Start

```bash
# Build the image
docker-compose build

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 6. Verify Deployment

```bash
# Test health endpoint
curl http://localhost:8000/health

# Should return: {"status":"healthy","version":"2.0.0"}
```

### 7. Configure Devices

Now you can add your plugs and servers:

```bash
# Using curl
curl -X POST http://localhost:8000/plugs \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"name":"server-plug","ip":"192.168.1.50"}'

curl -X POST http://localhost:8000/servers \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"name":"server1","hostname":"server1.local","mac":"AA:BB:CC:DD:EE:FF","plug":"server-plug"}'

# Or use the CLI client (see Client Installation Guide)
```

## Network Configuration

### Host Network Mode (Default)

The default configuration uses `network_mode: host` which allows the server to:
- Access LAN devices directly
- Discover smart plugs
- Send WOL packets
- SSH to servers

**Ports used:**
- `8000` - REST API

### Bridge Network Mode (Alternative)

If you need bridge mode:

1. Edit `docker-compose.yml`:
   ```yaml
   services:
     homelab-server:
       # network_mode: host  # Comment this out
       ports:
         - "8000:8000"
       networks:
         - homelab
   
   networks:
     homelab:
       driver: bridge
   ```

2. Ensure the container can reach your LAN

## Data Persistence

Configuration is stored in `./data/config.json` (automatically created).

**Backup your data:**
```bash
cp data/config.json data/config.json.backup
```

## Updating the Server

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

## Security Considerations

### 1. API Key Security

- Use a strong, random API key (32+ characters)
- Never commit `.env` file to version control
- Rotate keys periodically
- Use environment variables in production

### 2. Network Security

- Run behind a firewall
- Don't expose port 8000 to the internet
- Use VPN for remote access
- Consider using HTTPS with reverse proxy (nginx, Caddy)

### 3. SSH Configuration

For server shutdown functionality:

```bash
# Generate SSH key on Docker host
ssh-keygen -t ed25519 -C "homelab-server"

# Copy to target servers
ssh-copy-id user@target-server

# Test
ssh target-server sudo poweroff
```

Configure passwordless sudo on target servers:
```bash
# On each target server
echo "username ALL=(ALL) NOPASSWD: /sbin/poweroff" | sudo tee /etc/sudoers.d/poweroff
sudo chmod 0440 /etc/sudoers.d/poweroff
```

## Monitoring

### View Logs

```bash
# All logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific container
docker logs homelab-server -f
```

### Health Checks

The container includes built-in health checks:

```bash
# Check health status
docker inspect homelab-server --format='{{.State.Health.Status}}'

# View health check logs
docker inspect homelab-server --format='{{json .State.Health}}' | jq
```

### Resource Usage

```bash
# Container stats
docker stats homelab-server

# Disk usage
docker system df
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs

# Common issues:
# - Missing environment variables
# - Port 8000 already in use
# - Invalid Tapo credentials
```

### Can't access smart plugs

```bash
# Test from container
docker exec homelab-server ping 192.168.1.50

# If ping fails, check network configuration
```

### Telegram bot not working

```bash
# Check environment variables
docker exec homelab-server env | grep TELEGRAM

# Test bot token
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe

# View bot logs
docker-compose logs | grep telegram
```

### High CPU/Memory usage

```bash
# Check processes inside container
docker exec homelab-server ps aux

# Restart container
docker-compose restart
```

## Backup and Restore

### Backup

```bash
# Backup configuration
tar -czf homelab-backup-$(date +%Y%m%d).tar.gz data/

# Include environment file (careful with secrets!)
tar -czf homelab-full-backup-$(date +%Y%m%d).tar.gz data/ .env
```

### Restore

```bash
# Extract backup
tar -xzf homelab-backup-20260101.tar.gz

# Restart container
docker-compose restart
```

## Advanced Configuration

### Custom Config Path

```bash
# In docker-compose.yml
environment:
  - CONFIG_PATH=/custom/path/config.json
volumes:
  - /host/custom/path:/custom/path
```

### Multiple Instances

Run multiple instances for different networks:

```bash
# Create separate directories
mkdir -p ~/homelab-{home,office}

# Copy and customize docker-compose.yml for each
# Change ports and volumes

# Start each instance
cd ~/homelab-home && docker-compose up -d
cd ~/homelab-office && docker-compose up -d
```

### Reverse Proxy (nginx)

```nginx
server {
    listen 80;
    server_name homelab.local;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### HTTPS with Let's Encrypt

Use Caddy for automatic HTTPS:

```caddyfile
homelab.yourdomain.com {
    reverse_proxy localhost:8000
}
```

## Maintenance

### Log Rotation

Logs are automatically rotated (configured in docker-compose.yml):
- Max size: 10MB per file
- Max files: 3

### Updates

Check for updates regularly:

```bash
cd homelab-cli
git fetch
git log HEAD..origin/main --oneline

# If updates available
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

### Cleanup

```bash
# Remove unused images
docker image prune -a

# Remove stopped containers
docker container prune

# Full cleanup
docker system prune -a --volumes
```
