# CI/CD Pipeline Setup

This document describes how to configure the GitHub Actions CI/CD pipeline.

## Pipeline Overview

The pipeline runs on every push and pull request to `master`/`main`:

1. **Lint** - Syntax and style checks using ruff
2. **Type Check** - Static type analysis with pyright
3. **Test** - Run pytest with coverage (must be ≥50%)
4. **Deploy** - Deploy to Raspberry Pi via WireGuard VPN (only on master/main push)

## Required GitHub Secrets

Configure these secrets in your repository settings (Settings → Secrets and variables → Actions):

### WireGuard VPN Secrets

| Secret | Description | Example |
|--------|-------------|---------|
| `WG_PRIVATE_KEY` | Client private key for WireGuard | `4Kz...=` (base64) |
| `WG_PEER_PUBLIC_KEY` | Server's public key | `8Yz...=` (base64) |
| `WG_ENDPOINT` | WireGuard server endpoint | `vpn.example.com:51820` |
| `WG_CLIENT_IP` | IP address for the CI runner | `10.0.0.100` |
| `WG_ALLOWED_IPS` | Networks accessible via VPN | `10.0.0.0/24,192.168.1.0/24` |

### SSH & Deployment Secrets

| Secret | Description | Example |
|--------|-------------|---------|
| `RPI_SSH_PRIVATE_KEY` | SSH private key (ed25519 recommended) | `-----BEGIN OPENSSH...` |
| `RPI_HOST` | Raspberry Pi IP or hostname | `192.168.1.50` or `10.0.0.5` |
| `RPI_USER` | SSH username on the RPI | `pi` |
## Generating WireGuard Keys

```bash
# On the CI client (or locally to copy to secrets)
wg genkey | tee privatekey | wg pubkey > publickey

# privatekey contents → WG_PRIVATE_KEY
# publickey contents → add to server's [Peer] section
```

## Generating SSH Keys

```bash
# Generate a dedicated deploy key
ssh-keygen -t ed25519 -C "github-actions-deploy" -f deploy_key

# deploy_key contents → RPI_SSH_PRIVATE_KEY
# deploy_key.pub → add to RPI's ~/.ssh/authorized_keys
```

## Server-side WireGuard Config

Add this peer to your WireGuard server config (`/etc/wireguard/wg0.conf`):

```ini
[Peer]
# GitHub Actions CI
PublicKey = <CI_PUBLIC_KEY>
AllowedIPs = 10.0.0.100/32
```

Then reload: `sudo wg syncconf wg0 <(wg-quick strip wg0)`

## Local Deployment

For manual deployment without CI:

```bash
cd docker
./deploy.sh --build
```

## Troubleshooting

### WireGuard connection fails
- Verify endpoint is reachable from GitHub Actions (not behind CGNAT)
- Check firewall allows UDP on WireGuard port
- Ensure AllowedIPs includes the RPI network

### SSH connection fails
- Verify SSH key is in RPI's authorized_keys
- Check RPI is accessible via VPN (test with `ping`)
- Ensure DEPLOY_PATH exists and is writable

### Docker build fails on RPI
- Ensure Docker is installed: `docker --version`
- Ensure docker-compose is installed: `docker-compose --version`
- Check disk space: `df -h`
