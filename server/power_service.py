"""
Power Control Service - Orchestrates server power management
"""
import asyncio
import logging
import time
from typing import Dict, Callable, Optional
from .plug_service import PlugService
from .server_service import ServerService

logger = logging.getLogger(__name__)


class PowerControlService:
    """Controls server power with plug monitoring"""

    def __init__(self, plug_service: PlugService, server_service: ServerService):
        self.plug_service = plug_service
        self.server_service = server_service

    async def power_on(
        self,
        server: Dict,
        plug_ip: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """Power on a server with monitoring"""
        result = {"success": False, "message": "", "logs": []}

        def log(msg: str):
            result["logs"].append(msg)
            if progress_callback:
                progress_callback(msg)

        log("Turning on plug...")
        await self.plug_service.turn_on(plug_ip)
        log("Plug turned on")

        log("Monitoring server boot (60s)...")
        success = await self._monitor_boot(server, plug_ip, 60, log)

        if not success:
            power = await self.plug_service.get_power(plug_ip)
            log(f"Server not responding (power: {power:.1f}W)")

            if power < 5.0:
                log("Sending Wake-on-LAN packet...")
                self.server_service.send_wol(server["mac"])

                log("Monitoring server boot (60s)...")
                success = await self._monitor_boot(server, plug_ip, 60, log)

                if not success:
                    log("Server failed to boot")
                    log("Turning off plug...")
                    await self.plug_service.turn_off(plug_ip)
                    result["message"] = "Server failed to boot"
                    return result

        log("Server is online!")
        result["success"] = True
        result["message"] = "Server powered on successfully"
        return result

    async def _monitor_boot(
        self,
        server: Dict,
        plug_ip: str,
        duration: int,
        log_callback: Callable
    ) -> bool:
        """Monitor server boot process"""
        start = time.time()

        while time.time() - start < duration:
            passed = int(time.time() - start)
            
            if self.server_service.ping(server["hostname"]):
                log_callback("Server responding to ping!")
                return True

            try:
                power = await self.plug_service.get_power(plug_ip)
                log_callback(f"[{passed:02}s] Power: {power:.1f}W")
            except Exception as e:
                logger.warning(f"Failed to read power: {e}")

            await asyncio.sleep(2)

        return False

    async def power_off(
        self,
        server: Dict,
        plug_ip: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """Power off a server with monitoring"""
        result = {"success": False, "message": "", "logs": []}

        def log(msg: str):
            result["logs"].append(msg)
            if progress_callback:
                progress_callback(msg)

        log("Sending shutdown command...")
        try:
            self.server_service.shutdown(server["hostname"])
            log("Shutdown command sent")
        except Exception as e:
            log(f"Failed to send shutdown: {e}")
            log("Continuing with power monitoring...")

        log("Monitoring server shutdown...")
        start = time.time()
        timeout = 120
        timestamp_low_power = None

        while time.time() - start < timeout:
            passed = int(time.time() - start)
            
            try:
                power = await self.plug_service.get_power(plug_ip)
                log(f"[{passed:02}s] Power: {power:.1f}W")

                if power < 5.0:
                    if timestamp_low_power is None:
                        timestamp_low_power = time.time()
                    if time.time() - timestamp_low_power > 10:
                        log(f"Server powered down (power: {power:.1f}W)")
                        break
                else:
                    timestamp_low_power = None
            except Exception as e:
                logger.warning(f"Failed to read power: {e}")

            await asyncio.sleep(2)
        else:
            log("Timeout waiting for shutdown")

        log("Turning off plug...")
        await self.plug_service.turn_off(plug_ip)
        log("Server is offline")
        
        result["success"] = True
        result["message"] = "Server powered off successfully"
        return result
