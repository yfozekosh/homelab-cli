# Quick Start Guide

Get up and running with Homelab Management in 5 minutes!

## 🚀 Server Setup (5 minutes)

```bash
# 1. Clone and navigate
git clone <repository-url>
cd homelab-cli/docker

# 2. Create configuration
cp .env.example .env

# 3. Edit .env with your credentials
# Required: TAPO_USERNAME, TAPO_PASSWORD, API_KEY
# Optional: TELEGRAM_BOT_TOKEN, TELEGRAM_USER_IDS
nano .env

# 4. Start server
docker-compose up -d

# 5. Verify it's running
curl http://localhost:8000/health
```

## 💻 Client Setup (2 minutes)

```bash
# 1. Navigate to client directory
cd ../client

# 2. Run installer
./install.sh
# (Follow prompts to enter server URL and API key)

# 3. Test
lab config test
```

## 🤖 Telegram Bot Setup (Optional)

```bash
# 1. Create bot with @BotFather on Telegram
# 2. Get your user ID from @userinfobot
# 3. Add to .env file:
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_USER_IDS=your_user_id_here

# 4. Restart server
docker-compose restart

# 5. Start bot in Telegram with /start
```

## 📝 First Steps

### Add a Smart Plug

```bash
lab plug add my-plug 192.168.1.50
```

### Add a Server

```bash
lab server add myserver myserver.local AA:BB:CC:DD:EE:FF my-plug
```

### Check Status

```bash
lab server list
```

### Power Control

```bash
# Power on
lab on myserver

# Power off
lab off myserver

# Check status
lab status

# Live monitoring with smooth in-place updates (every 5 seconds)
lab status -f

# Custom refresh intervals
lab status -f 0.5    # Fast: every 500ms
lab status -f 60     # Slow: every minute
```

**Tip:** Live monitoring uses efficient ANSI cursor positioning to update only changed values without screen flicker! Press **'q'** or **Ctrl+C** to exit.

### Cost Tracking

```bash
# Set electricity price (EUR or USD per kWh)
lab set price 0.2721

# Check current price setting
lab get price

# Status will now show costs
lab status
```

**Example output with price set:**
```
Current: 45.2W (0.0123€/h)
Today: 543Wh (0.1477€)
Month: 15.2kWh (4.1359€)
```

## 📱 Using Telegram Bot

1. Open Telegram and search for your bot
2. Send `/start`
3. Click "🖥️ Servers"
4. Select a server
5. Use "⚡ Power On" or "🔴 Power Off" buttons

## 🔑 Configuration Details

### Generating API Key

```bash
# Use one of these methods:
openssl rand -hex 32
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Environment Variables

Edit `docker/.env`:

```bash
# Required
TAPO_USERNAME=your_email@example.com
TAPO_PASSWORD=your_tapo_password
API_KEY=your_generated_api_key

# Optional (for Telegram)
TELEGRAM_BOT_TOKEN=123456789:ABC...
TELEGRAM_USER_IDS=123456789,987654321
```

### SSH Setup (for server shutdown)

```bash
# On Docker host, copy SSH key to servers
ssh-copy-id user@target-server

# Configure passwordless sudo on target server
echo "username ALL=(ALL) NOPASSWD: /sbin/poweroff" | sudo tee /etc/sudoers.d/poweroff
```

## 🐛 Common Issues

### Cannot connect to server
```bash
# Check if server is running
docker-compose ps

# Check logs
docker-compose logs -f
```

### Smart plug not responding
- Verify IP address: `ping 192.168.1.50`
- Check Tapo credentials in `.env`
- Ensure server can reach LAN devices

### Telegram bot not responding
- Verify token is correct
- Check your user ID is in TELEGRAM_USER_IDS
- View logs: `docker-compose logs | grep telegram`

## 📚 Next Steps

- Read the full [README](../README.md)
- Check [Server Deployment Guide](SERVER_DEPLOYMENT.md)
- Review [Client Installation Guide](CLIENT_INSTALLATION.md)

## 💡 Tips

- Use tab completion: `lab <TAB>`
- View API docs: http://your-server:8000/docs
- Monitor logs: `docker-compose logs -f`
- Backup config: `cp docker/data/config.json backup/`

## 🎯 Example Workflow

```bash
# Morning routine
lab on workstation
lab on testserver

# Check status
lab server list

# Evening routine
lab off workstation
lab off testserver
```

Happy homelabbing! 🏠✨
