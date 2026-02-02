# CLI Client Installation Guide

This guide covers installing and configuring the Homelab CLI client.

## Prerequisites

- Python 3.7 or higher
- pip3
- Network access to the Homelab server

## Quick Installation

### Automated Installation

```bash
cd client
./install.sh
```

The script will:
1. Check Python version
2. Install dependencies
3. Copy client to `~/.local/bin/lab`
4. Prompt for server URL and API key
5. Test the connection

### Manual Installation

```bash
# Install dependencies
pip3 install --user requests

# Copy client script
cp client/lab.py ~/.local/bin/lab
chmod +x ~/.local/bin/lab

# Add to PATH if needed
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Configure
lab config set-server http://your-server:8000
lab config set-key your-api-key

# Test connection
lab config test
```

## Configuration

### Server URL

Set the server URL where your Homelab server is running:

```bash
lab config set-server http://192.168.1.100:8000
```

### API Key

Set the API key (must match the server's API_KEY):

```bash
lab config set-key your-api-key-here
```

### Environment Variables

Alternatively, use environment variables:

```bash
export HOMELAB_SERVER_URL=http://192.168.1.100:8000
export HOMELAB_API_KEY=your-api-key-here
```

Add to `~/.bashrc` or `~/.zshrc` for persistence:

```bash
echo 'export HOMELAB_SERVER_URL=http://192.168.1.100:8000' >> ~/.bashrc
echo 'export HOMELAB_API_KEY=your-api-key-here' >> ~/.bashrc
source ~/.bashrc
```

### Configuration File

Configuration is stored in `~/.config/homelab-client/config.json`:

```json
{
  "server_url": "http://192.168.1.100:8000",
  "api_key": "your-api-key"
}
```

**Priority:**
1. Command-line arguments (if implemented)
2. Environment variables
3. Configuration file

## Usage

### Configuration Commands

```bash
# Set server URL
lab config set-server http://192.168.1.100:8000

# Set API key
lab config set-key your-api-key

# Test connection
lab config test
```

### Plug Management

```bash
# List all plugs
lab plug list

# Add a new plug
lab plug add office-plug 192.168.1.50

# Remove a plug
lab plug remove office-plug
```

### Server Management

```bash
# List all servers
lab server list

# Add a new server (without plug)
lab server add server1 server1.local AA:BB:CC:DD:EE:FF

# Add a server with associated plug
lab server add server2 server2.local AA:BB:CC:DD:EE:00 office-plug

# Remove a server
lab server remove server1
```

### Power Control

```bash
# Power on a server
lab on server1

# Power off a server
lab off server1

# Show status of all devices
lab status

# Live monitoring with efficient in-place updates (press 'q' or Ctrl+C to stop)
lab status -f           # Default: 5 second refresh

# Custom refresh intervals
lab status -f 0.5       # Fast: 500 milliseconds
lab status -f 10        # Moderate: 10 seconds  
lab status -f 60        # Slow: 1 minute
```

**Performance Note:** The live monitoring mode uses ANSI terminal control codes to update only the lines that changed, providing smooth, flicker-free updates without clearing the screen. Exit by pressing **'q'** or **Ctrl+C**.

### Energy Cost Tracking

```bash
# Set your electricity price (per kWh in EUR/USD)
lab set price 0.2721

# View current price setting
lab get price

# Status will automatically show cost calculations
lab status
```

**How it works:**
- Current power cost per hour calculated from instantaneous power draw
- Daily and monthly costs calculated from energy usage (Wh)
- Costs displayed alongside energy metrics in status output
- Example: `Current: 45.2W (0.0123€/h)` or `Today: 543Wh (0.1477€)`

### Help

```bash
# General help
lab --help

# Command-specific help
lab plug --help
lab server --help
```

## Examples

### Complete Setup Workflow

```bash
# 1. Install client
cd client && ./install.sh

# 2. Add smart plugs
lab plug add office-plug 192.168.1.50
lab plug add lab-plug 192.168.1.51

# 3. Add servers
lab server add workstation workstation.local AA:BB:CC:DD:EE:FF office-plug
lab server add testserver test.local 11:22:33:44:55:66 lab-plug

# 4. Check status
lab server list

# 5. Power on a server
lab on workstation

# 6. Power off a server
lab off workstation
```

### Daily Usage

```bash
# Morning: start work server
lab on workstation

# Check all servers
lab server list

# Evening: shutdown
lab off workstation
```

## Troubleshooting

### Command not found

```bash
# Check if installed
which lab

# If not found, check PATH
echo $PATH | grep ".local/bin"

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### Connection refused

```bash
# Test connection
lab config test

# Check server is running
curl http://your-server:8000/health

# Check firewall
telnet your-server 8000
```

### Invalid API key

```bash
# Verify API key matches server
lab config set-key correct-api-key

# Or check environment variable
echo $HOMELAB_API_KEY
```

### Python version issues

```bash
# Check Python version (need 3.7+)
python3 --version

# If too old, install newer version
# Ubuntu/Debian
sudo apt install python3.10

# CentOS/RHEL
sudo yum install python39
```

### Dependency issues

```bash
# Install requests manually
pip3 install --user --upgrade requests

# If pip fails, try
python3 -m pip install --user requests

# Check installation
python3 -c "import requests; print(requests.__version__)"
```

## Multiple Servers

### Different Environments

You can manage multiple Homelab servers by switching configuration:

```bash
# Home server
export HOMELAB_SERVER_URL=http://192.168.1.100:8000
export HOMELAB_API_KEY=home-api-key
lab server list

# Office server
export HOMELAB_SERVER_URL=http://10.0.0.100:8000
export HOMELAB_API_KEY=office-api-key
lab server list
```

### Shell Aliases

Create aliases for different environments:

```bash
# Add to ~/.bashrc
alias lab-home='HOMELAB_SERVER_URL=http://192.168.1.100:8000 HOMELAB_API_KEY=home-key lab'
alias lab-office='HOMELAB_SERVER_URL=http://10.0.0.100:8000 HOMELAB_API_KEY=office-key lab'

# Usage
lab-home server list
lab-office server list
```

## Advanced Usage

### Scripting

The CLI is designed for scripting:

```bash
#!/bin/bash
# start-workday.sh

echo "Starting workday servers..."
lab on workstation
sleep 10
lab on testserver

# Check status
lab server list
```

### Cron Jobs

Automate server management:

```bash
# Add to crontab
crontab -e

# Power on at 8 AM on weekdays
0 8 * * 1-5 /home/user/.local/bin/lab on workstation

# Power off at 6 PM on weekdays
0 18 * * 1-5 /home/user/.local/bin/lab off workstation
```

### Error Handling

```bash
#!/bin/bash
# robust-power-on.sh

if lab on $1; then
    echo "Successfully powered on $1"
    # Send notification
    notify-send "Server $1 is starting"
else
    echo "Failed to power on $1"
    exit 1
fi
```

## Updating

### Update Client

```bash
# Pull latest from repository
cd homelab-cli
git pull

# Reinstall
cd client
./install.sh
```

### Manual Update

```bash
# Download new version
cp client/lab.py ~/.local/bin/lab
chmod +x ~/.local/bin/lab

# Update dependencies if needed
pip3 install --user --upgrade requests
```

## Uninstallation

```bash
# Remove client
rm ~/.local/bin/lab

# Remove configuration
rm -rf ~/.config/homelab-client

# Remove Python package (optional)
pip3 uninstall requests
```

## Security Best Practices

### API Key Storage

```bash
# Don't hardcode in scripts
# Bad:
lab config set-key my-secret-key

# Good: use environment variable
export HOMELAB_API_KEY=$(cat ~/.secrets/homelab-api-key)
```

### File Permissions

```bash
# Secure config file
chmod 600 ~/.config/homelab-client/config.json

# Secure API key file
chmod 600 ~/.secrets/homelab-api-key
```

### SSH Keys

For shutdown functionality:

```bash
# Generate dedicated key
ssh-keygen -t ed25519 -f ~/.ssh/homelab_key -C "homelab-automation"

# Copy to servers
ssh-copy-id -i ~/.ssh/homelab_key user@server
```

## Platform-Specific Notes

### macOS

```bash
# Install Python if needed
brew install python3

# Installation same as Linux
cd client && ./install.sh
```

### Windows (WSL)

```bash
# Use Windows Subsystem for Linux
# Installation same as Linux
cd client && ./install.sh
```

### Windows (Native)

```powershell
# Install Python from python.org

# Install dependencies
pip install requests

# Copy script
copy client\lab.py %USERPROFILE%\lab.py

# Use with Python
python %USERPROFILE%\lab.py server list
```

## Support

For issues:
1. Check troubleshooting section
2. Verify server is accessible
3. Test with curl/httpie
4. Check GitHub issues
5. Enable debug output (if available)
