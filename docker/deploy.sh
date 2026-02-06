#!/bin/bash
# Deploy script for Homelab Server
# Usage: ./deploy.sh
set -e

# Generate build info
echo "Generating build info..."
pushd ..

# Gather Git info (defaults to 'unknown' if git fails)
COMMIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
COMMIT_DATE=$(git log -1 --format=%cd 2>/dev/null || echo "unknown")
COMMIT_MSG=$(git log -1 --format=%s 2>/dev/null || echo "unknown")
BUILD_DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Read latest changes if file exists
LATEST_CHANGES=""
if [ -f "LATEST_CHANGES.md" ]; then
    LATEST_CHANGES=$(cat LATEST_CHANGES.md)
fi

mkdir -p server

# Create JSON using jq for safe escaping
jq -n \
  --arg sha "$COMMIT_SHA" \
  --arg cdate "$COMMIT_DATE" \
  --arg bdate "$BUILD_DATE" \
  --arg msg "$COMMIT_MSG" \
  --arg changes "$LATEST_CHANGES" \
  '{
    commit_sha: $sha,
    commit_date: $cdate,
    build_date: $bdate,
    commit_message: $msg,
    latest_changes: $changes
  }' > server/build_info.json

echo "server/build_info.json generated"
popd

docker compose build 
pushd /opt/stacks/homelab-server/ 
docker compose down 
docker compose up -d 
popd
