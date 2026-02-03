#!/bin/bash
# Test SSH connectivity and sudo permissions

SERVER="192.168.1.107"  # main-srv hostname

echo "=== Testing SSH Connection ==="
echo "1. Basic SSH connectivity:"
ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$SERVER" "echo 'SSH works'" 2>&1
echo "Exit code: $?"
echo

echo "2. Testing sudo permissions:"
ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$SERVER" "sudo -n echo 'Sudo works'" 2>&1
echo "Exit code: $?"
echo

echo "3. Testing sudo poweroff (DRY RUN - will not actually shutdown):"
ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$SERVER" "sudo -n poweroff --help" 2>&1 | head -5
echo "Exit code: $?"
echo

echo "=== Troubleshooting Tips ==="
echo "If 'Permission denied (publickey)' - need to set up SSH keys"
echo "If 'sudo: a password is required' - need to configure NOPASSWD in sudoers"
echo "Add to /etc/sudoers on the server: $USER ALL=(ALL) NOPASSWD: /sbin/poweroff"
