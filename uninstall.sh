#!/bin/bash
# Uninstallation script for Lab CLI tool

set -e

echo "Uninstalling Lab CLI tool..."
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
VENV_DIR="$HOME/.local/share/lab-venv"
BIN_FILE="$HOME/.local/bin/lab"
CONFIG_DIR="$HOME/.config/lab"

echo "Found the following Lab components:"
echo ""
[ -d "$VENV_DIR" ] && echo "  ✓ Virtual environment: $VENV_DIR"
[ -f "$BIN_FILE" ] && echo "  ✓ Executable: $BIN_FILE"
[ -d "$CONFIG_DIR" ] && echo "  ✓ Configuration: $CONFIG_DIR"
echo ""

# Confirm uninstallation
if ! confirm "Do you want to uninstall Lab CLI?"; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Remove virtual environment
if [ -d "$VENV_DIR" ]; then
    echo "Removing virtual environment..."
    rm -rf "$VENV_DIR"
    echo "  ✓ Removed $VENV_DIR"
fi

# Remove executable
if [ -f "$BIN_FILE" ]; then
    echo "Removing executable..."
    rm -f "$BIN_FILE"
    echo "  ✓ Removed $BIN_FILE"
fi

# Ask about configuration
if [ -d "$CONFIG_DIR" ]; then
    echo ""
    echo "Configuration directory contains:"
    ls -lh "$CONFIG_DIR" 2>/dev/null || true
    echo ""
    
    if confirm "Do you want to remove configuration and logs (including plug/server data)?"; then
        rm -rf "$CONFIG_DIR"
        echo "  ✓ Removed $CONFIG_DIR"
    else
        echo "  ⊘ Kept configuration at $CONFIG_DIR"
        echo "    (You can manually delete it later if needed)"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ Lab CLI tool uninstalled successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Manual cleanup (optional):"
echo ""
echo "1. Remove environment variables from ~/.bashrc:"
echo "   - PATH=\"\$HOME/.local/bin:\$PATH\""
echo "   - TAPO_USERNAME"
echo "   - TAPO_PASSWORD"
echo ""
echo "2. Remove Python packages (if not used by other tools):"
echo "   pip3 uninstall tapo-py3 wakeonlan"
echo ""
