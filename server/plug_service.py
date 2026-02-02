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
            raise ValueError("TAPO_USERNAME and TAPO_PASSWORD environment variables must be set")

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
