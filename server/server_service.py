"""
Server management service
"""

import subprocess
import socket
import logging
import os
from wakeonlan import send_magic_packet

logger = logging.getLogger(__name__)


class ServerService:
    """Handles server operations like ping, resolve, WOL, and shutdown"""

    def __init__(self):
        # Get SSH username from environment, default to current user
        self.ssh_user = os.getenv("SSH_USER", os.getenv("USER", "root"))
        logger.info(f"SSH user configured as: {self.ssh_user}")

    def _build_ssh_target(self, hostname: str) -> str:
        """Build SSH target with user@hostname format"""
        return f"{self.ssh_user}@{hostname}"

    def test_ssh_connection(self, hostname: str) -> bool:
        """Test if SSH connection works"""
        try:
            target = self._build_ssh_target(hostname)
            result = subprocess.run(
                [
                    "ssh",
                    "-o",
                    "BatchMode=yes",
                    "-o",
                    "ConnectTimeout=5",
                    "-o",
                    "StrictHostKeyChecking=no",
                    target,
                    "echo test",
                ],
                timeout=10,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"SSH connection test failed: {e}")
            return False

    def test_sudo_poweroff(self, hostname: str) -> bool:
        """Test if sudo poweroff works without password"""
        try:
            target = self._build_ssh_target(hostname)
            result = subprocess.run(
                [
                    "ssh",
                    "-o",
                    "BatchMode=yes",
                    "-o",
                    "ConnectTimeout=5",
                    "-o",
                    "StrictHostKeyChecking=no",
                    target,
                    "sudo -n poweroff --help",
                ],
                timeout=10,
                capture_output=True,
                text=True,
            )
            # Check if command succeeded and didn't ask for password
            return (
                result.returncode == 0 and "password is required" not in result.stderr
            )
        except Exception as e:
            logger.error(f"Sudo test failed: {e}")
            return False

    def resolve_hostname(self, hostname: str) -> str:
        """Resolve hostname to IP address"""
        try:
            return socket.gethostbyname(hostname)
        except socket.gaierror:
            return "Unable to resolve"

    def ping(self, hostname: str, timeout: int = 1) -> bool:
        """Ping a server"""
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", str(timeout), hostname],
                capture_output=True,
                timeout=timeout + 1,
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Ping failed: {e}")
            return False

    def send_wol(self, mac: str):
        """Send Wake-on-LAN packet"""
        logger.info(f"Sending WOL packet to {mac}")
        send_magic_packet(mac)

    def shutdown(self, hostname: str):
        """Ping a server"""
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", str(timeout), hostname],
                capture_output=True,
                timeout=timeout + 1,
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Ping failed: {e}")
            return False

    def send_wol(self, mac: str):
        """Send Wake-on-LAN packet"""
        logger.info(f"Sending WOL packet to {mac}")
        send_magic_packet(mac)

    def shutdown(self, hostname: str):
        """Send shutdown command to server"""
        target = self._build_ssh_target(hostname)
        logger.info(f"Sending shutdown command to {target}")
        try:
            # Use -o BatchMode=yes to avoid password prompts
            # Use -o StrictHostKeyChecking=no to avoid interactive prompts
            result = subprocess.run(
                [
                    "ssh",
                    "-o",
                    "BatchMode=yes",
                    "-o",
                    "ConnectTimeout=10",
                    "-o",
                    "StrictHostKeyChecking=no",
                    target,
                    "sudo poweroff",
                ],
                timeout=15,
                capture_output=True,
                text=True,
            )
            logger.info(f"SSH shutdown result: return code {result.returncode}")

            # Log output for debugging
            if result.stdout:
                logger.info(f"SSH stdout: {result.stdout}")
            if result.stderr:
                logger.info(f"SSH stderr: {result.stderr}")

            # Exit codes: 0 = success, 255 = connection closed (expected during shutdown)
            if result.returncode != 0 and result.returncode != 255:
                error_msg = f"SSH command failed with exit code {result.returncode}"
                if result.stderr:
                    error_msg += f": {result.stderr.strip()}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except subprocess.TimeoutExpired:
            # Timeout is expected as server shuts down mid-command
            logger.info("SSH command timed out (expected during shutdown)")
        except FileNotFoundError:
            error_msg = "SSH command not found - is OpenSSH installed?"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            # Re-raise with context
            if "SSH command failed" in str(e) or "not found" in str(e):
                raise
            logger.error(f"Unexpected error during shutdown: {e}")
            raise Exception(f"Failed to send shutdown: {e}")

    def resolve_hostname(self, hostname: str) -> str:
        """Resolve hostname to IP address"""
        try:
            result = subprocess.run(
                ["nslookup", hostname], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.split("\n")
                for line in lines:
                    if "Address:" in line and "#53" not in line:
                        return line.split("Address:")[1].strip()
        except Exception as e:
            logger.warning(f"nslookup failed for {hostname}: {e}")
        return "Unable to resolve"
