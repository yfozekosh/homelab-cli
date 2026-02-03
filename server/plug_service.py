"""
Plug Management Service
"""

import os
import logging
from typing import Optional
from tapo import ApiClient

logger = logging.getLogger(__name__)


class PlugService:
    """Manages Tapo smart plugs"""

    def __init__(self):
        self.username = os.getenv("TAPO_USERNAME")
        self.password = os.getenv("TAPO_PASSWORD")

        if not self.username or not self.password:
            raise ValueError(
                "TAPO_USERNAME and TAPO_PASSWORD environment variables must be set"
            )

    async def get_client(self, ip: str):
        """Get Tapo client for a plug"""
        client = ApiClient(self.username, self.password)
        device = await client.p110(ip)
        return device

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
        device = await self.get_client(ip)
        info = await device.get_device_info()
        return {
            "on": info.device_on,
            "signal_level": info.signal_level,
        }

    async def get_energy_usage(self, ip: str) -> dict:
        """Get energy usage statistics"""
        try:
            device = await self.get_client(ip)

            # Current power
            current = await device.get_current_power()

            # Energy usage
            energy = await device.get_energy_usage()

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
        device = await self.get_client(ip)
        info = await device.get_device_info()

        # Get energy data
        energy_data = await self.get_energy_usage(ip)

        return {"on": info.device_on, "signal_level": info.signal_level, **energy_data}
