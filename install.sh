#!/bin/bash
# Installation script for Lab CLI tool - Cross-platform (Fedora/Debian/Raspbian)

set -e

echo "Installing Lab CLI tool..."

# Detect OS and install dependencies
echo "Detecting operating system..."
if [ -f /etc/fedora-release ]; then
  echo "✓ Fedora detected"
  echo "Installing system dependencies..."
  sudo dnf install -y python3 python3-pip bind-utils openssh-clients
elif [ -f /etc/debian_version ]; then
  DISTRO=$(cat /etc/os-release | grep ^NAME= | cut -d'"' -f2)
  echo "✓ $DISTRO detected"
  echo "Installing system dependencies..."
  #sudo apt update
  #sudo apt install -y python3 python3-pip python3-venv dnsutils openssh-client iputils-ping
else
  echo "✓ Unknown distribution detected"
  echo "⚠ Make sure these are installed: python3, pip, ssh, ping, nslookup"
fi

# Create virtual environment (optional but recommended)
if [ ! -d "$HOME/.local/share/lab-venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$HOME/.local/share/lab-venv"
fi

# Activate virtual environment
source "$HOME/.local/share/lab-venv/bin/activate"

# Install Python dependencies
echo "Installing Python dependencies..."
#pip install --upgrade pip
pip install tapo wakeonlan

# Copy lab script
echo "Installing lab command..."
mkdir -p "$HOME/.local/bin"
mkdir -p "$HOME/.config/lab"

# Copy actual script to venv
cp lab.py "$HOME/.local/share/lab-venv/lab-cli.py"

# Create wrapper script that activates venv
cat >"$HOME/.local/bin/lab" <<'EOF'
#!/bin/bash
source "$HOME/.local/share/lab-venv/bin/activate"
python3 "$HOME/.local/share/lab-venv/lab-cli.py" "$@"
EOF

chmod +x "$HOME/.local/bin/lab"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
  echo ""
  echo "⚠ Add the following to your ~/.bashrc:"
  echo 'export PATH="$HOME/.local/bin:$PATH"'
  echo ""
  echo "Then run: source ~/.bashrc"
fi

# Create environment file template
cat >"$HOME/.config/lab/env.example" <<'EOF'
# Tapo credentials - Add these to your ~/.bashrc
export TAPO_USERNAME="your-tapo-email@example.com"
export TAPO_PASSWORD="your-tapo-password"
EOF

echo ""
echo "✓ Installation complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Next steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Add to your ~/.bashrc:"
echo ""
echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
echo "   export TAPO_USERNAME='your-email@example.com'"
echo "   export TAPO_PASSWORD='your-password'"
echo ""
echo "2. Reload your shell:"
echo "   source ~/.bashrc"
echo ""
echo "3. Test the installation:"
echo "   lab plug list"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Usage examples:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  lab plug add homelab 192.168.1.100"
echo "  lab server add srv1 server1.local AA:BB:CC:DD:EE:FF homelab"
echo "  lab server list"
echo "  lab on srv1"
echo "  lab off srv1"
echo ""
