# Changelog

All notable changes to the Homelab Management project will be documented in this file.

## [2.0.0] - 2026-02-02

### 🎉 Major Rework - Server-Client Architecture

Complete redesign from monolithic CLI to distributed server-client system.

### Added

#### Server Component
- **FastAPI REST API** with comprehensive endpoints for all operations
- **Telegram Bot** with interactive inline keyboard buttons
  - Real-time power monitoring updates
  - User whitelist authentication
  - Confirmation dialogs for critical actions
- **Docker support** with docker-compose for easy deployment
- **API key authentication** for secure access
- **Health check endpoint** for monitoring
- **Auto-generated API documentation** (Swagger/ReDoc)
- **Modular service architecture**:
  - `config.py` - Configuration management
  - `plug_service.py` - Smart plug operations
  - `server_service.py` - Server management (WOL, ping, shutdown)
  - `power_service.py` - Power control orchestration
  - `telegram_bot.py` - Telegram bot implementation

#### CLI Client
- **Lightweight Python client** with minimal dependencies
- **Easy installation** with automated script
- **Connection health check** on startup
- **Configuration management** via file and environment variables
- **Same command structure** as legacy version for familiarity
- Stores config in `~/.config/homelab-client/config.json`

#### Docker Setup
- Multi-stage Dockerfile for optimization
- docker-compose.yml with host network mode
- Persistent volume for configuration
- Health checks and logging configuration
- Automatic restart policy

#### Documentation
- Comprehensive README with architecture overview
- Server Deployment Guide with security best practices
- Client Installation Guide with troubleshooting
- Quick Start Guide for 5-minute setup
- API documentation via FastAPI auto-docs

#### Telegram Bot Features
- `/start` - Welcome message and main menu
- `/menu` - Show main menu
- `/servers` - List all servers with status indicators
- `/plugs` - List all smart plugs
- Interactive buttons for all operations
- Real-time progress updates during power operations
- Server status indicators (🟢 Online / 🔴 Offline)
- Confirmation dialog for power off operations
- Navigation between menus
- User-friendly error messages

### Changed

- **Architecture**: Monolithic → Server-Client
- **Authentication**: Environment variables → API keys + Telegram whitelist
- **Configuration**: Local file → Centralized server storage
- **Deployment**: Direct Python → Docker containerized
- **Communication**: Direct hardware access → REST API
- **Interface**: CLI only → CLI + Telegram Bot + REST API

### Improved

- **Security**: Added API key authentication and Telegram user whitelist
- **Scalability**: Multiple clients can connect to single server
- **Monitoring**: Real-time power consumption during operations
- **User Experience**: Interactive Telegram bot with buttons
- **Installation**: Simple one-script client installation
- **Maintenance**: Centralized configuration and logging
- **Documentation**: Comprehensive guides for all components

### Migration Notes

For users of version 1.x:

1. **Server Setup Required**: The new version requires running a server (Docker recommended)
2. **Configuration Migration**: Configuration format has changed
   - Old: `~/.config/lab/config.json`
   - New: Server stores config in `/app/data/config.json`
   - Client config: `~/.config/homelab-client/config.json`
3. **New Dependencies**: Server needs TAPO credentials and API key
4. **Client Changes**: 
   - Must point to server URL
   - Needs API key for authentication
5. **Legacy Support**: Old `lab.py` renamed to `lab.py.legacy`

### Technical Details

**Server Stack:**
- FastAPI (async REST API)
- python-telegram-bot (bot framework)
- tapo-py3 (smart plug API)
- wakeonlan (WOL packets)
- uvicorn (ASGI server)

**Client Stack:**
- requests (HTTP client)
- Minimal dependencies for easy installation

**Docker:**
- Base: python:3.11-slim
- Network: host mode (for LAN access)
- Persistent storage: volume mount

### Security Enhancements

- API key authentication for all endpoints
- Telegram user ID whitelist
- Environment variable configuration (no hardcoded secrets)
- SSH key authentication for server shutdown
- Docker isolation

### Breaking Changes

- ⚠️ Complete rewrite - not backward compatible with 1.x
- Command structure preserved but server connection required
- Environment variables changed:
  - Old: `TAPO_USERNAME`, `TAPO_PASSWORD` (client-side)
  - New: Same variables but server-side, plus `API_KEY`
  - Client: `HOMELAB_SERVER_URL`, `HOMELAB_API_KEY`

### Removed

- Direct smart plug access from CLI (now via server)
- Local configuration in CLI (now centralized on server)
- Virtual environment installation (client has minimal deps)

### Known Issues

None at release. Please report issues on GitHub.

### Future Enhancements

Planned for future versions:
- Web UI dashboard
- Historical power consumption tracking
- Scheduled power operations
- Email/push notifications
- Multi-server support
- HTTPS/TLS support
- Database backend (SQLite/PostgreSQL)
- Additional smart device support

---

## [1.0.0] - Previous Release

### Features
- Direct Tapo smart plug control
- Server management with WOL and shutdown
- Power monitoring during boot/shutdown
- Configuration stored locally
- Single Python script

---

For upgrade instructions, see [docs/QUICK_START.md](docs/QUICK_START.md)
