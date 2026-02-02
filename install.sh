#!/bin/bash
# Legacy installation script - redirects to new client installer
set -e

echo "================================================================"
echo " Homelab CLI has been restructured!"
echo "================================================================"
echo ""
echo "The project now has a server-client architecture:"
echo ""
echo "  Server:  FastAPI + Telegram Bot (runs in Docker)"
echo "  Client:  Lightweight CLI tool"
echo ""
echo "Please use the new installation:"
echo ""
echo "  For server:  See docs/SERVER_DEPLOYMENT.md"
echo "  For client:  cd client && ./install.sh"
echo ""
echo "================================================================"
echo ""

read -p "Would you like to install the CLI client now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "client/install.sh" ]; then
        cd client
        ./install.sh
    else
        echo "Error: client/install.sh not found"
        echo "Please run from the repository root"
        exit 1
    fi
else
    echo "Installation cancelled."
    echo "For manual installation, see docs/CLIENT_INSTALLATION.md"
fi
