#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Homelab CLI Client Installation${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: Python 3 is not installed${NC}"
    echo "Please install Python 3 and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓${NC} Python 3 found: $(python3 --version)"

# Check Python version (need 3.7+)
MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 7 ]); then
    echo -e "${RED}❌ Error: Python 3.7 or higher is required${NC}"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  pip3 not found, attempting to install...${NC}"
    python3 -m ensurepip --default-pip || {
        echo -e "${RED}❌ Failed to install pip${NC}"
        exit 1
    }
fi

echo -e "${GREEN}✓${NC} pip3 found"

# Installation directory
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

# Check if installation directory is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo -e "${YELLOW}⚠️  $INSTALL_DIR is not in PATH${NC}"
    echo "Add the following line to your ~/.bashrc or ~/.zshrc:"
    echo ""
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

# Determine source location
if [ -f "./client/lab.py" ]; then
    SOURCE_FILE="./client/lab.py"
elif [ -f "./lab.py" ]; then
    SOURCE_FILE="./lab.py"
else
    echo -e "${YELLOW}⚠️  Client script not found locally, downloading from repository...${NC}"
    
    # Try to download from GitHub (adjust URL as needed)
    # For now, we'll just exit if not found locally
    echo -e "${RED}❌ Error: Cannot find lab.py${NC}"
    echo "Please run this script from the repository root or client directory"
    exit 1
fi

# Copy client script
echo "Installing client to $INSTALL_DIR/lab..."
cp "$SOURCE_FILE" "$INSTALL_DIR/lab"
chmod +x "$INSTALL_DIR/lab"
echo -e "${GREEN}✓${NC} Client script installed"

# Install dependencies
echo "Installing dependencies..."
pip3 install --user requests >/dev/null 2>&1 || {
    echo -e "${YELLOW}⚠️  Failed to install with --user flag, trying without...${NC}"
    pip3 install requests >/dev/null 2>&1 || {
        echo -e "${RED}❌ Failed to install dependencies${NC}"
        exit 1
    }
}
echo -e "${GREEN}✓${NC} Dependencies installed"

# Configuration
echo ""
echo -e "${GREEN}Configuration${NC}"
echo "-------------"

# Check if config already exists
CONFIG_DIR="$HOME/.config/homelab-client"
CONFIG_FILE="$CONFIG_DIR/config.json"

if [ -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}⚡ Existing configuration found${NC}"
    echo ""
    
    # Try to read existing values
    if command -v jq &> /dev/null; then
        EXISTING_SERVER=$(jq -r '.server_url // empty' "$CONFIG_FILE" 2>/dev/null)
        if [ -n "$EXISTING_SERVER" ]; then
            echo "Current server: $EXISTING_SERVER"
        fi
    fi
    
    echo ""
    read -p "Keep existing configuration? (Y/n): " KEEP_CONFIG
    
    if [[ ! $KEEP_CONFIG =~ ^[Nn]$ ]]; then
        echo -e "${GREEN}✓${NC} Keeping existing configuration"
        SKIP_CONFIG=true
    else
        SKIP_CONFIG=false
    fi
else
    SKIP_CONFIG=false
fi

if [ "$SKIP_CONFIG" = false ]; then
    # Ask for server URL
    read -p "Enter server URL (e.g., http://192.168.1.100:8000): " SERVER_URL
    if [ -z "$SERVER_URL" ]; then
        echo -e "${YELLOW}⚠️  Server URL not provided${NC}"
        echo "You can set it later with: lab config set-server <url>"
    else
        "$INSTALL_DIR/lab" config set-server "$SERVER_URL" >/dev/null 2>&1 || {
            echo -e "${YELLOW}⚠️  Failed to save server URL${NC}"
        }
    fi

    # Ask for API key
    read -sp "Enter API key: " API_KEY
    echo ""
    if [ -z "$API_KEY" ]; then
        echo -e "${YELLOW}⚠️  API key not provided${NC}"
        echo "You can set it later with: lab config set-key <key>"
    else
        "$INSTALL_DIR/lab" config set-key "$API_KEY" >/dev/null 2>&1 || {
            echo -e "${YELLOW}⚠️  Failed to save API key${NC}"
        }
    fi

    # Test connection if both provided
    if [ -n "$SERVER_URL" ] && [ -n "$API_KEY" ]; then
        echo ""
        echo "Testing connection to server..."
        if "$INSTALL_DIR/lab" config test >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Connection successful!"
        else
            echo -e "${YELLOW}⚠️  Cannot connect to server${NC}"
            echo "Please check your server URL and API key"
        fi
    fi
fi

# Success message
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Usage examples:"
echo "  lab server list              # List all servers"
echo "  lab on <server>              # Power on a server"
echo "  lab off <server>             # Power off a server"
echo "  lab plug list                # List all plugs"
echo ""
echo "For help: lab --help"
echo ""

if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo -e "${YELLOW}⚠️  Remember to add $INSTALL_DIR to your PATH${NC}"
    echo ""
fi
