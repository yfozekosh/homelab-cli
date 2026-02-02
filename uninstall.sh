#!/bin/bash
# Uninstallation script for Homelab CLI

set -e

echo "================================================================"
echo " Homelab CLI Uninstaller"
echo "================================================================"
echo ""

# Function to ask for confirmation
confirm() {
    read -p "$1 [y/N]: " response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Check what's installed
OLD_VENV_DIR="$HOME/.local/share/lab-venv"
OLD_CONFIG_DIR="$HOME/.config/lab"
NEW_BIN_FILE="$HOME/.local/bin/lab"
NEW_CONFIG_DIR="$HOME/.config/homelab-client"

echo "Checking for installed components..."
echo ""

FOUND_OLD=false
FOUND_NEW=false

# Check for old installation
if [ -d "$OLD_VENV_DIR" ] || [ -d "$OLD_CONFIG_DIR" ]; then
    FOUND_OLD=true
    echo "Found OLD version components:"
    [ -d "$OLD_VENV_DIR" ] && echo "  ✓ Virtual environment: $OLD_VENV_DIR"
    [ -d "$OLD_CONFIG_DIR" ] && echo "  ✓ Configuration: $OLD_CONFIG_DIR"
    echo ""
fi

# Check for new installation
if [ -f "$NEW_BIN_FILE" ] || [ -d "$NEW_CONFIG_DIR" ]; then
    FOUND_NEW=true
    echo "Found NEW version components:"
    [ -f "$NEW_BIN_FILE" ] && echo "  ✓ Executable: $NEW_BIN_FILE"
    [ -d "$NEW_CONFIG_DIR" ] && echo "  ✓ Configuration: $NEW_CONFIG_DIR"
    echo ""
fi

if ! $FOUND_OLD && ! $FOUND_NEW; then
    echo "No Lab/Homelab CLI installation found."
    exit 0
fi

# Confirm uninstallation
if ! confirm "Do you want to uninstall Homelab CLI?"; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Remove old version
if $FOUND_OLD; then
    echo ""
    echo "Removing OLD version..."
    
    if [ -d "$OLD_VENV_DIR" ]; then
        rm -rf "$OLD_VENV_DIR"
        echo "  ✓ Removed $OLD_VENV_DIR"
    fi
    
    if [ -d "$OLD_CONFIG_DIR" ]; then
        if confirm "Remove old configuration at $OLD_CONFIG_DIR?"; then
            rm -rf "$OLD_CONFIG_DIR"
            echo "  ✓ Removed $OLD_CONFIG_DIR"
        else
            echo "  ⊘ Kept $OLD_CONFIG_DIR"
        fi
    fi
fi

# Remove new version
if $FOUND_NEW; then
    echo ""
    echo "Removing NEW version..."
    
    if [ -f "$NEW_BIN_FILE" ]; then
        rm -f "$NEW_BIN_FILE"
        echo "  ✓ Removed $NEW_BIN_FILE"
    fi
    
    if [ -d "$NEW_CONFIG_DIR" ]; then
        if confirm "Remove client configuration at $NEW_CONFIG_DIR?"; then
            rm -rf "$NEW_CONFIG_DIR"
            echo "  ✓ Removed $NEW_CONFIG_DIR"
        else
            echo "  ⊘ Kept $NEW_CONFIG_DIR"
        fi
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Homelab CLI uninstalled successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Manual cleanup (optional):"
echo ""
echo "1. Remove environment variables from ~/.bashrc (if set):"
echo "   - HOMELAB_SERVER_URL"
echo "   - HOMELAB_API_KEY"
echo "   - TAPO_USERNAME (old version)"
echo "   - TAPO_PASSWORD (old version)"
echo ""
echo "2. Remove Python packages (if not used elsewhere):"
echo "   pip3 uninstall requests tapo-py3 wakeonlan"
echo ""
echo "3. Stop and remove Docker server (if running):"
echo "   cd docker && docker-compose down -v"
echo ""
