# Homelab Management (homelab-cli)

Homelab Management is a small server + CLI stack for managing homelab machines and Tapo smart plugs on a local network. It provides a FastAPI REST API used by a Python CLI client and an optional Telegram bot for interactive control.

## What this repository contains

- **Server** (`server/`): FastAPI application that exposes the REST API.
- **Telegram bot** (`server/telegram_bot.py`, `server/bot/`): Optional bot that talks to the same services as the API.
- **CLI client** (`client/`): Python command-line tool (`lab`) that calls the API.
- **Docker deployment** (`docker/`): Dockerfile and compose file for running the server locally.

## Capabilities

- Manage Tapo smart plugs (add/remove/list, switch on/off, read power metrics where supported).
- Manage servers (inventory, ping checks, Wake-on-LAN, and remote shutdown over SSH).
- Show a consolidated status view, including power and energy reporting.
- Optional Telegram bot with a button-driven menu (restricted by a user ID allowlist).

## Prerequisites

- Docker Engine and Docker Compose (for running the server locally)
- Python 3.7+ and pip (for the CLI client)
- Network reachability from the server host to:
  - Tapo devices on your LAN
  - Your target servers (for ping/WOL and optional SSH shutdown)

## Local deployment with Docker

The recommended way to run the server is via Docker Compose.

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd homelab-cli
   ```

2. Configure environment variables:

   ```bash
   cd docker
   cp .env.example .env
   ${EDITOR:-nano} .env
   ```

   Minimum required values:

   - `TAPO_USERNAME`
   - `TAPO_PASSWORD`
   - `API_KEY`

   Optional (Telegram bot):

   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_USER_IDS`

3. Start the service:

   ```bash
   # Docker Compose v2
   docker compose up -d --build

   # If your environment still uses the v1 plugin
   # docker-compose up -d --build
   ```

4. Verify it is running:

   ```bash
   curl http://localhost:8000/health
   ```

5. View logs:

   ```bash
   docker compose logs -f
   ```

### Notes on networking

The compose file uses `network_mode: host` so the container can reach LAN devices directly (smart plugs, WOL broadcast, SSH to servers). If you change this to bridge networking you will need to map ports and ensure the container can still reach your LAN.

### Persistent configuration

The server stores its configuration in a JSON file mounted from `docker/data/`:

- Host path: `docker/data/config.json`
- Container path: `/app/data/config.json` (via `CONFIG_PATH`)

## Install the CLI client

The client is a lightweight Python CLI called `lab`.

### Option A: Install using the provided script (recommended)

```bash
cd client
./install.sh
```

The script:

- Installs runtime dependencies (currently `requests`)
- Copies `lab` and the `homelab_client` package to `~/.local/bin/`
- Optionally prompts for server URL and API key

Make sure `~/.local/bin` is in your `PATH`.

### Option B: Manual installation

```bash
pip3 install --user requests

mkdir -p ~/.local/bin
cp client/lab.py ~/.local/bin/lab
chmod +x ~/.local/bin/lab

# Ensure ~/.local/bin is in PATH (bash example)
# echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
# source ~/.bashrc
```

### Configure the client

```bash
lab config set-server http://<server-ip>:8000
lab config set-key <api-key>
lab config test
```

Client configuration is stored at `~/.config/homelab-client/config.json`. You can also use:

```bash
export HOMELAB_SERVER_URL=http://<server-ip>:8000
export HOMELAB_API_KEY=<api-key>
```

## Example client usage

A typical workflow looks like this:

```bash
# Add a smart plug
lab plug add office-plug 192.168.1.50

# Add a server (MAC is required for Wake-on-LAN)
lab server add workstation workstation.local AA:BB:CC:DD:EE:FF office-plug

# List inventory
lab plug list
lab server list

# Power control
lab on workstation
lab off workstation

# Consolidated status (follow mode refreshes continuously)
lab status
lab status -f

# Optional: set electricity price per kWh so status includes cost estimates
lab set price 0.2721
lab get price
```

## Telegram bot

The Telegram bot is optional. When enabled, it provides an interactive menu for viewing servers/plugs and running power actions.

### Enable the bot

1. Create a bot via `@BotFather` and copy the token.
2. Get your Telegram numeric user ID (for example via `@userinfobot`).
3. Set the following in `docker/.env`:

   ```bash
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_USER_IDS=123456789,987654321
   ```

4. Restart the container:

   ```bash
   cd docker
   docker compose restart
   ```

5. Open a chat with your bot and send `/start`.

### Access control

The bot is restricted to the comma-separated list of user IDs in `TELEGRAM_USER_IDS`. Requests from other users are rejected.

## API and security

- All API endpoints require an API key via the `X-API-Key` header.
- API docs are available when the server is running:
  - Swagger UI: `http://<server-ip>:8000/docs`
  - ReDoc: `http://<server-ip>:8000/redoc`

## SSH-based shutdown

Remote shutdown uses SSH from inside the container. The compose file mounts the host SSH directory read-only and the container startup script copies keys into place.

Requirements:

- Your Docker host must have working SSH access to the target machines.
- Configure passwordless `sudo poweroff` on the target machines if required.
- Set `SSH_USER` in `docker/.env` if the SSH username differs from the host user.

## Documentation

- Server deployment: `docs/SERVER_DEPLOYMENT.md`
- Client installation: `docs/CLIENT_INSTALLATION.md`
- Architecture notes: `docs/ARCHITECTURE.md`

## License

See `LICENSE`.
