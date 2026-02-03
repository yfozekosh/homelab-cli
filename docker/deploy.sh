#!/bin/bash
# Deploy script for Homelab Server
# Usage: ./deploy.sh
set -e
docker compose build 
pushd /opt/stacks/homelab-server/ 
docker compose down 
docker compose up -d 
popd
