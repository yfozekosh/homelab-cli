# SSH Sudo Configuration for Homelab

## Problem
The shutdown command fails because `sudo poweroff` requires a password.

## Solution
Configure passwordless sudo for the poweroff command on each server.

## Steps

### Option 1: Allow poweroff without password (Recommended)

1. SSH into the server:
   ```bash
   ssh 192.168.1.107
   ```

2. Edit sudoers file:
   ```bash
   sudo visudo
   ```

3. Add this line at the end:
   ```
   yfozekosh ALL=(ALL) NOPASSWD: /sbin/poweroff, /usr/sbin/poweroff
   ```

4. Save and exit (Ctrl+X, then Y, then Enter if using nano)

5. Test it:
   ```bash
   sudo -n poweroff --help
   ```
   Should show help without asking for password.

### Option 2: Allow all sudo commands without password (Less secure)

Instead of the line above, use:
```
yfozekosh ALL=(ALL) NOPASSWD: ALL
```

### Repeat for all servers
Do this on each server you want to control:
- main-srv (192.168.1.107)
- dell-srv2 (192.168.1.111)

## Verification

After configuration, test from the homelab server:
```bash
ssh -o BatchMode=yes 192.168.1.107 "sudo -n poweroff --help"
```

Should work without errors.

## Security Note
This allows the user to shutdown the server without a password. 
Ensure SSH key authentication is properly secured.
