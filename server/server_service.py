"""
Server Management Service
"""

import logging
import subprocess
from wakeonlan import send_magic_packet

logger = logging.getLogger(__name__)


class ServerService:
    """Manages servers (WOL, shutdown, ping)"""

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
        """Send shutdown command to server"""
        logger.info(f"Sending shutdown command to {hostname}")
        try:
            # Use -o BatchMode=yes to avoid password prompts
            # Use -o StrictHostKeyChecking=no to avoid interactive prompts
            # Run in background with nohup to avoid hanging
            result = subprocess.run(
                [
                    "ssh",
                    "-o",
                    "BatchMode=yes",
                    "-o",
                    "ConnectTimeout=10",
                    "-o",
                    "StrictHostKeyChecking=no",
                    hostname,
                    "sudo poweroff",
                ],
                timeout=15,
                capture_output=True,
                text=True,
            )
            logger.info(f"SSH shutdown result: {result.returncode}")
            if result.returncode != 0 and result.returncode != 255:
                # 255 is expected when connection closes due to shutdown
                logger.warning(f"SSH stderr: {result.stderr}")
        except subprocess.TimeoutExpired:
            # Timeout is expected as server shuts down
            logger.info("SSH command timed out (expected during shutdown)")
        except Exception as e:
            logger.error(f"Failed to send shutdown: {e}")
            raise

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
