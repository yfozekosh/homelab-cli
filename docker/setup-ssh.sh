#!/bin/bash
# Setup script for Docker SSH configuration

set -e

echo "=== Homelab Docker SSH Setup ==="
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Must run from docker/ directory"
    echo "   cd /home/yfozekosh/temp/homelab-cli/docker"
    exit 1
fi

# Get current user
CURRENT_USER=${USER}
echo "Current user: $CURRENT_USER"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✓ .env created"
else
    echo "✓ .env already exists"
fi

# Check if SSH_USER is set
if grep -q "^SSH_USER=" .env; then
    EXISTING_USER=$(grep "^SSH_USER=" .env | cut -d= -f2)
    echo "SSH_USER already set to: $EXISTING_USER"
    read -p "Update to '$CURRENT_USER'? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sed -i "s/^SSH_USER=.*/SSH_USER=$CURRENT_USER/" .env
        echo "✓ Updated SSH_USER to $CURRENT_USER"
    fi
else
    echo "Adding SSH_USER=$CURRENT_USER to .env..."
    echo "" >> .env
    echo "# SSH Configuration" >> .env
    echo "SSH_USER=$CURRENT_USER" >> .env
    echo "✓ SSH_USER added"
fi

echo ""
echo "=== SSH Keys Check ==="
if [ -f "$HOME/.ssh/id_rsa" ] || [ -f "$HOME/.ssh/id_ed25519" ]; then
    echo "✓ SSH keys found"
else
    echo "⚠️  No SSH keys found in ~/.ssh/"
    echo "   Generate with: ssh-keygen -t ed25519"
fi

echo ""
echo "=== Restarting Docker Container ==="
docker-compose down
docker-compose up -d
sleep 3

echo ""
echo "=== Checking Configuration ==="
docker-compose logs --tail=20 | grep "SSH user configured" || echo "⚠️  SSH user log not found"

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Next steps:"
echo "1. Test SSH health: homelab config ssh-healthcheck"
echo "2. Configure sudo on servers (see docs/SUDO_SETUP.md)"
echo "3. Test power operations: homelab power off <server-name>"
echo ""
