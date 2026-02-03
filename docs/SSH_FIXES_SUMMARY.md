# SSH Configuration Summary

## All Issues Fixed ✅

### 1. ~~SSH connecting as root instead of user~~ ✅
**Fix:** Added `SSH_USER` environment variable, server uses `user@hostname` format

### 2. ~~SSH keys not accessible in Docker~~ ✅
**Fix:** Mount `~/.ssh` to `/host-ssh`, copy files with correct permissions in `start.sh`

### 3. ~~"Bad owner or permissions on /root/.ssh/config"~~ ✅
**Fix:** Copy files (not mount), set chmod 600 on all SSH files

### 4. ~~SSH asks "Are you sure you want to continue connecting?"~~ ✅
**Fix:** Auto-generate SSH config with:
```
StrictHostKeyChecking no
UserKnownHostsFile /dev/null
LogLevel ERROR
```

## Complete Setup Commands

```bash
# 1. Configure environment
cd /home/yfozekosh/temp/homelab-cli/docker
cp .env.example .env
# Edit .env: SSH_USER=yfozekosh

# 2. Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 3. Check logs
docker-compose logs | grep -A 6 "Setting up SSH"

# 4. Test from container
docker exec homelab-server ssh $SSH_USER@192.168.1.107 "echo test"

# 5. Test health check
homelab config ssh-healthcheck

# 6. Test power operation
homelab power off main-srv
```

## Expected Container Logs

```
Setting up SSH keys...
  ✓ Copied id_rsa
  ✓ Copied known_hosts
  ✓ Copied user config
  ✓ Configured SSH to skip host verification
SSH setup complete
SSH user configured as: yfozekosh
Starting API server on port 8000...
```

## Files Modified

- `docker/docker-compose.yml` - Mount `/host-ssh` instead of `/root/.ssh`
- `docker/start.sh` - Copy SSH files with correct permissions, generate config
- `docker/.env.example` - Added SSH_USER
- `server/server_service.py` - Read SSH_USER, use `user@hostname` format
- `docs/DOCKER_SSH_SETUP.md` - Complete documentation
- `docs/QUICKSTART_DOCKER_SSH.md` - Quick start guide
- `docs/SUDO_SETUP.md` - Sudo configuration guide

## SSH Test Matrix

| Test | Expected Result |
|------|----------------|
| `ssh user@host "echo test"` from host | ✓ Works |
| `docker exec ... ssh user@host "echo test"` | ✓ Works |
| SSH asks about host key | ✗ Never asks |
| SSH permission errors | ✗ No errors |
| `homelab config ssh-healthcheck` | ✓ All pass |
| `homelab power off <server>` | ✓ Real-time logs |

## Troubleshooting

**No logs about SSH setup**
→ Container needs rebuild: `docker-compose build --no-cache`

**Still getting permission errors**
→ Old container running: `docker-compose down && docker-compose up -d`

**SSH user shows as root**
→ SSH_USER not in .env file

**Still prompts for host verification**
→ Check `/root/.ssh/config` inside container: `docker exec homelab-server cat /root/.ssh/config`

## Next Steps

After SSH works, configure sudo on servers:
1. See `docs/SUDO_SETUP.md`
2. Add passwordless sudo for poweroff command
3. Test with `homelab config ssh-healthcheck`
