"""
Plug Management Service
"""

import asyncio
import logging
import os
import time

from tapo import ApiClient

logger = logging.getLogger(__name__)


class PlugService:
    """Manages Tapo smart plugs"""

    def __init__(self):
        username = os.getenv("TAPO_USERNAME")
        password = os.getenv("TAPO_PASSWORD")

        if not username or not password:
            raise ValueError(
                "TAPO_USERNAME and TAPO_PASSWORD environment variables must be set"
            )

        self.username = username
        self.password = password

    async def get_client(self, ip: str, timeout: float = 1.5):
        """Get Tapo client for a plug"""
        try:
            client = ApiClient(self.username, self.password)
            device = await asyncio.wait_for(client.p110(ip), timeout=timeout)
            return device
        except asyncio.TimeoutError:
            logger.warning(f"Timeout connecting to plug at {ip}")
            raise
        except Exception as e:
            logger.warning(f"Failed to connect to plug at {ip}: {e}")
            raise

    async def turn_on(self, ip: str):
        """Turn on a plug"""
        logger.info(f"Turning on plug at {ip}")
        device = await self.get_client(ip)
        await device.on()
        logger.info(f"Plug at {ip} turned on")

    async def turn_off(self, ip: str):
        """Turn off a plug"""
        logger.info(f"Turning off plug at {ip}")
        device = await self.get_client(ip)
        await device.off()
        logger.info(f"Plug at {ip} turned off")

    async def get_power(self, ip: str) -> float:
        """Get current power usage in watts"""
        device = await self.get_client(ip)
        energy = await device.get_current_power()
        return energy.current_power

    async def get_status(self, ip: str) -> dict:
        """Get plug status"""
        try:
            device = await self.get_client(ip, timeout=1.5)
            info = await asyncio.wait_for(device.get_device_info(), timeout=1.5)
            return {
                "on": info.device_on,
                "signal_level": info.signal_level,
            }
        except Exception as e:
            logger.warning(f"Failed to get status for {ip}: {e}")
            return {"on": False, "signal_level": 0}

    async def get_energy_usage(self, ip: str) -> dict:
        """Get energy usage statistics"""
        try:
            device = await self.get_client(ip, timeout=1.5)

            # Current power
            current = await asyncio.wait_for(device.get_current_power(), timeout=1.5)

            # Energy usage
            energy = await asyncio.wait_for(device.get_energy_usage(), timeout=1.5)

            return {
                "current_power": current.current_power,  # Watts
                "today_runtime": energy.today_runtime,  # Minutes
                "today_energy": energy.today_energy,  # Wh
                "month_runtime": energy.month_runtime,  # Minutes
                "month_energy": energy.month_energy,  # Wh
            }
        except Exception as e:
            logger.warning(f"Failed to get energy usage for {ip}: {e}")
            return {
                "current_power": 0,
                "today_runtime": 0,
                "today_energy": 0,
                "month_runtime": 0,
                "month_energy": 0,
            }

    async def get_full_status(self, ip: str) -> dict:
        """Get complete status including energy data"""
        t0 = time.monotonic()
        try:
            device = await self.get_client(ip, timeout=1.5)

            # Get device info and energy data in parallel from same connection
            info_task = asyncio.wait_for(device.get_device_info(), timeout=1.5)
            power_task = asyncio.wait_for(device.get_current_power(), timeout=1.5)
            energy_task = asyncio.wait_for(device.get_energy_usage(), timeout=1.5)

            info, current, energy = await asyncio.gather(
                info_task, power_task, energy_task
            )

            elapsed = time.monotonic() - t0
            logger.debug(
                "get_full_status %s: done in %.2fs (power=%.1fW, on=%s)",
                ip,
                elapsed,
                current.current_power,
                info.device_on,
            )

            return {
                "on": info.device_on,
                "signal_level": info.signal_level,
                "current_power": current.current_power,
                "today_runtime": energy.today_runtime,
                "today_energy": energy.today_energy,
                "month_runtime": energy.month_runtime,
                "month_energy": energy.month_energy,
            }
        except Exception as e:
            elapsed = time.monotonic() - t0
            logger.warning("get_full_status %s: failed after %.2fs: %s", ip, elapsed, e)
            return {
                "on": False,
                "signal_level": 0,
                "current_power": 0,
                "today_runtime": 0,
                "today_energy": 0,
                "month_runtime": 0,
                "month_energy": 0,
            }
