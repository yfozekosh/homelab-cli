# Homelab Management System

A complete server-client architecture for managing Tapo smart plugs and homelab servers with power monitoring, Wake-on-LAN, and remote shutdown capabilities.

## 🏗️ Architecture

- **Server**: FastAPI REST API + Telegram Bot (runs in Docker)
- **Client**: Lightweight Python CLI tool
- **Telegram Bot**: Full-featured bot with inline keyboard buttons

## ✨ Features

- 🔌 **Smart Plug Management**: Control Tapo P110 smart plugs
- 🖥️ **Server Management**: Wake-on-LAN, shutdown, and ping monitoring
- ⚡ **Power Monitoring**: Real-time power consumption tracking during boot/shutdown
- 🤖 **Telegram Bot**: Interactive bot with button-based UI
- 🔐 **Security**: API key authentication & Telegram user whitelist
- 🐳 **Docker**: Easy deployment with docker-compose

## 📋 Prerequisites

- Docker and docker-compose (for server)
- Python 3.7+ (for CLI client)
- Tapo smart plugs (P110 or compatible)
- Telegram account (optional, for bot)

## 🚀 Quick Start

### 1. Server Deployment

```bash
# Clone the repository
git clone <repository-url>
cd homelab-cli

# Configure environment
cd docker
cp .env.example .env
nano .env  # Edit with your credentials

# Start the server
docker-compose up -d

# Check logs
docker-compose logs -f
```

### 2. Client Installation

```bash
# Run the installation script
cd ../client
./install.sh

# Or manually
pip3 install --user requests
cp lab.py ~/.local/bin/lab
chmod +x ~/.local/bin/lab

# Configure
lab config set-server http://your-server:8000
lab config set-key your-api-key
lab config test
```

**Note:** The install script detects existing configuration during reinstalls. Just press Enter to keep your current settings, or type 'n' to reconfigure.

### 3. Telegram Bot Setup

1. Create a bot with [@BotFather](https://t.me/botfather)
2. Get your Telegram user ID from [@userinfobot](https://t.me/userinfobot)
3. Add credentials to `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=123456789:ABCdef...
   TELEGRAM_USER_IDS=123456789,987654321
   ```
4. Restart the server: `docker-compose restart`
5. Start the bot: `/start` in Telegram

## 📖 Usage

### CLI Commands

#### Configuration
```bash
lab config set-server <url>   # Set server URL
lab config set-key <key>      # Set API key
lab config test               # Test connection
```

#### Plug Management
```bash
lab plug list                 # List all plugs
lab plug add <name> <ip>      # Add a plug
lab plug edit <name> <ip>     # Edit plug IP
lab plug remove <name>        # Remove a plug
```

#### Server Management
```bash
lab server list                              # List all servers
lab server add <name> <hostname> [mac] [plug]  # Add a server (MAC optional)
lab server edit <name> [--hostname H] [--mac M] [--plug P]  # Edit server
lab server remove <name>                     # Remove a server
```

#### Power Control
```bash
lab on <server>               # Power on a server
lab off <server>              # Power off a server
lab status                    # Show comprehensive status of all devices
lab status -f                 # Live monitoring with in-place updates (every 5s)
lab status -f 0.5             # Fast refresh every 500ms
lab status -f 60              # Slow refresh every minute
```

**Note:** Live monitoring (`-f`) uses efficient in-place updates - only changed data is redrawn, no screen clearing or flicker. Press **'q'** or **Ctrl+C** to exit.

#### Settings
```bash
lab set price 0.2721          # Set electricity price per kWh (EUR or USD)
lab get price                 # Get current electricity price
```

**Note:** Once a price is set, the status command will automatically calculate and display energy costs alongside power consumption metrics.

### Telegram Bot

1. **Start the bot**: `/start` or `/menu`
2. **View servers**: Click "🖥️ Servers"
3. **Select a server**: Click on server name
4. **Power control**: Use "⚡ Power On" or "🔴 Power Off" buttons
5. **View plugs**: Click "🔌 Plugs"

The bot provides real-time updates during power operations!

**Note**: If a server doesn't have a MAC address configured, the bot will show a warning and direct you to use the CLI to add it.

## 💡 Usage Examples

### Initial Setup
```bash
# Add a plug
lab plug add office-plug 192.168.1.50

# Add a server without MAC (configure later)
lab server add workstation workstation.local

# Add MAC address later
lab server edit workstation --mac AA:BB:CC:DD:EE:FF

# Associate with a plug
lab server edit workstation --plug office-plug
```

### Changing Configuration
```bash
# Change plug IP address
lab plug edit office-plug 192.168.1.55

# Update server hostname
lab server edit workstation --hostname ws.local

# Change associated plug
lab server edit workstation --plug new-plug
```

### Complete Server Setup
```bash
# Add server with all details
lab server add testserver test.local AA:BB:CC:DD:EE:FF lab-plug

# Or add incrementally
lab server add testserver test.local
lab server edit testserver --mac AA:BB:CC:DD:EE:FF
lab server edit testserver --plug lab-plug
```

## 🔧 Configuration

### Server Configuration

Edit `docker/.env`:

```bash
# Tapo Credentials
TAPO_USERNAME=your_email@example.com
TAPO_PASSWORD=your_password

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_USER_IDS=123456789,987654321  # Comma-separated

# API Security
API_KEY=your-secure-api-key
```

### Client Configuration

Configuration is stored in `~/.config/homelab-client/config.json`:

```json
{
  "server_url": "http://192.168.1.100:8000",
  "api_key": "your-api-key"
}
```

Or use environment variables:
```bash
export HOMELAB_SERVER_URL=http://192.168.1.100:8000
export HOMELAB_API_KEY=your-api-key
```

## 🐳 Docker Configuration

### Network Mode

The server uses `host` network mode to access LAN devices (smart plugs, servers). If you need to change this:

1. Switch to bridge mode in `docker-compose.yml`
2. Map port 8000
3. Ensure the container can reach your LAN devices

### Persistent Data

Server configuration is stored in `docker/data/config.json` (mounted as volume).

### Health Checks

The container includes a health check endpoint at `/health`.

## 🔒 Security

### API Key Authentication

All API endpoints require the `X-API-Key` header. Set a strong API key in `.env`.

### Telegram User Whitelist

Only users with IDs listed in `TELEGRAM_USER_IDS` can use the bot.

### SSH Key Setup

For server shutdown functionality, configure SSH key authentication:

```bash
# On the server host machine
ssh-copy-id user@target-server

# Test
ssh target-server sudo poweroff
```

Configure passwordless sudo for `poweroff`:
```bash
# On target server
echo "username ALL=(ALL) NOPASSWD: /sbin/poweroff" | sudo tee /etc/sudoers.d/poweroff
```

## 📊 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://your-server:8000/docs
- **ReDoc**: http://your-server:8000/redoc

## 🛠️ Development

### Project Structure

```
homelab-cli/
├── server/               # Server code
│   ├── main.py          # FastAPI application
│   ├── telegram_bot.py  # Telegram bot
│   ├── config.py        # Configuration manager
│   ├── plug_service.py  # Plug management
│   ├── server_service.py # Server management
│   ├── power_service.py # Power control orchestration
│   └── requirements.txt
├── client/              # CLI client
│   ├── homelab_client/  # Core client package (modular)
│   │   ├── __init__.py      # Package initialization
│   │   ├── client.py        # Main client facade
│   │   ├── cli.py           # CLI argument parsing
│   │   ├── config.py        # Configuration management
│   │   ├── api_client.py    # HTTP API client
│   │   ├── plug_manager.py  # Plug operations
│   │   ├── server_manager.py # Server operations
│   │   ├── power_manager.py # Power control
│   │   ├── price_manager.py # Electricity price
│   │   └── status_manager.py # Status monitoring
│   ├── lab.py           # Entry point script
│   ├── status_display.py # Status display logic
│   ├── install.sh       # Installation script
│   ├── requirements.txt
│   └── tests/           # Test suite (62 tests, 83% coverage)
│       ├── conftest.py
│       ├── test_*.py    # Modular test files
│       └── README.md    # Test documentation
├── docker/              # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── start.sh
│   └── .env.example
└── docs/                # Documentation
```

### Client Architecture

The client uses a modular, multi-class architecture following SOLID principles:

- **`HomelabClient`** - Main facade class that composes all managers
- **`ConfigManager`** - Configuration file management
- **`APIClient`** - Base HTTP client for all API communication
- **`PlugManager`** - Smart plug CRUD operations
- **`ServerManager`** - Server CRUD operations
- **`PowerManager`** - Power on/off operations
- **`PriceManager`** - Electricity price management
- **`StatusManager`** - Status monitoring with follow mode

**Benefits:**
- Single Responsibility: Each class has one clear purpose
- Easy Testing: Components can be tested in isolation
- Maintainability: Changes are contained to specific modules
- Extensibility: New features can be added without modifying existing code

### Testing

The client includes comprehensive unit tests with **83% coverage**.

```bash
cd client

# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_plug_operations.py -v

# Run tests with verbose output
pytest -v

# View coverage report
open htmlcov/index.html  # or xdg-open on Linux
```

**Test Statistics:**
- **62 tests** across 15 modular files
- **83% coverage** for client package
- **100% pass rate**
- **~1.75s** execution time

See [`client/tests/README.md`](client/tests/README.md) for detailed documentation.

### Running Locally (without Docker)

```bash
# Install dependencies
cd server
pip install -r requirements.txt

# Set environment variables
export TAPO_USERNAME=...
export TAPO_PASSWORD=...
export API_KEY=...

# Run server
python -m uvicorn main:app --reload

# Run bot (in another terminal)
python telegram_bot.py
```

## 🐛 Troubleshooting

### Cannot connect to server
- Check server is running: `docker-compose ps`
- Verify firewall allows port 8000
- Test with curl: `curl http://server:8000/health`

### Telegram bot not responding
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Check your user ID is in `TELEGRAM_USER_IDS`
- View logs: `docker-compose logs -f`

### Smart plug not responding
- Verify plug IP address is correct
- Check Tapo credentials in `.env`
- Ensure server can reach plug on LAN

### Server won't boot with WOL
- Verify MAC address is correct
- Enable WOL in server BIOS
- Check network card supports WOL

### SSH shutdown fails
- Verify SSH key authentication is working
- Check passwordless sudo is configured
- Test manually: `ssh server sudo poweroff`

## 📚 Documentation

- [Server Deployment Guide](docs/SERVER_DEPLOYMENT.md)
- [Client Installation Guide](docs/CLIENT_INSTALLATION.md)

## 📝 License

See LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.

## 📧 Support

For issues and questions, please use the GitHub issue tracker.