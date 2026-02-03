"""
Status Service - Aggregates status information for all devices
"""

import logging
from datetime import datetime
from typing import Dict, List
from .config import Config
from .plug_service import PlugService
from .server_service import ServerService

logger = logging.getLogger(__name__)


class StatusService:
    """Service for getting comprehensive status of all devices"""

    def __init__(
        self, config: Config, plug_service: PlugService, server_service: ServerService
    ):
        self.config = config
        self.plug_service = plug_service
        self.server_service = server_service

    def _format_duration(self, start_iso: str) -> str:
        """Format duration from ISO timestamp to human readable"""
        try:
            start = datetime.fromisoformat(start_iso)
            now = datetime.utcnow()
            delta = now - start

            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)

            parts = []
            if days > 0:
                parts.append(f"{days}d")
            if hours > 0:
                parts.append(f"{hours}h")
            if minutes > 0 or not parts:
                parts.append(f"{minutes}m")

            return " ".join(parts)
        except Exception as e:
            logger.warning(f"Failed to format duration: {e}")
            return "unknown"

    async def get_plug_status(self, name: str, plug_data: Dict) -> Dict:
        """Get detailed status for a single plug"""
        try:
            status = await self.plug_service.get_full_status(plug_data["ip"])

            # Calculate runtime in hours from minutes
            today_hours = status["today_runtime"] / 60 if status["today_runtime"] else 0
            month_hours = status["month_runtime"] / 60 if status["month_runtime"] else 0

            # Get electricity price
            price = self.config.get_electricity_price()

            # Calculate costs (energy in Wh, convert to kWh for cost)
            today_cost = (status["today_energy"] / 1000) * price if price > 0 else 0
            month_cost = (status["month_energy"] / 1000) * price if price > 0 else 0
            current_cost_per_hour = (
                (status["current_power"] / 1000) * price if price > 0 else 0
            )

            return {
                "name": name,
                "ip": plug_data["ip"],
                "online": True,
                "state": "on" if status["on"] else "off",
                "current_power": round(status["current_power"], 1),
                "current_cost_per_hour": round(current_cost_per_hour, 4),
                "today_energy": round(status["today_energy"], 1),
                "today_cost": round(today_cost, 4),
                "today_runtime": round(today_hours, 1),
                "month_energy": round(status["month_energy"], 1),
                "month_cost": round(month_cost, 4),
                "month_runtime": round(month_hours, 1),
            }
        except Exception as e:
            logger.error(f"Failed to get status for plug {name}: {e}")
            return {
                "name": name,
                "ip": plug_data["ip"],
                "online": False,
                "error": str(e),
            }

    async def get_server_status(self, name: str, server_data: Dict) -> Dict:
        """Get detailed status for a single server"""
        # Check if server is online
        online = self.server_service.ping(server_data["hostname"])

        # Update state tracking
        self.config.update_server_state(name, online)

        # Get state info
        state = self.config.get_server_state(name)

        result = {
            "name": name,
            "hostname": server_data["hostname"],
            "mac": server_data.get("mac", ""),
            "plug": server_data.get("plug"),
            "online": online,
            "ip": self.server_service.resolve_hostname(server_data["hostname"]),
        }

        # Add uptime/downtime info
        if state and state.get("last_change"):
            duration = self._format_duration(state["last_change"])
            if online:
                result["uptime"] = duration
            else:
                result["downtime"] = duration

        # Get plug power info if associated
        if server_data.get("plug"):
            plug = self.config.get_plug(server_data["plug"])
            if plug:
                try:
                    plug_status = await self.plug_service.get_full_status(plug["ip"])

                    # Get electricity price for cost calculations
                    price = self.config.get_electricity_price()
                    today_cost = (
                        (plug_status["today_energy"] / 1000) * price if price > 0 else 0
                    )
                    month_cost = (
                        (plug_status["month_energy"] / 1000) * price if price > 0 else 0
                    )
                    current_cost_per_hour = (
                        (plug_status["current_power"] / 1000) * price
                        if price > 0
                        else 0
                    )

                    result["power"] = {
                        "current": round(plug_status["current_power"], 1),
                        "current_cost_per_hour": round(current_cost_per_hour, 4),
                        "today_energy": round(plug_status["today_energy"], 1),
                        "today_cost": round(today_cost, 4),
                        "month_energy": round(plug_status["month_energy"], 1),
                        "month_cost": round(month_cost, 4),
                    }
                except Exception as e:
                    logger.warning(f"Failed to get power info for {name}: {e}")

        return result

    async def get_all_status(self) -> Dict:
        """Get comprehensive status of all servers and plugs"""
        plugs_status = []
        servers_status = []

        # Get all plugs status
        plugs = self.config.list_plugs()
        for name, plug_data in plugs.items():
            plug_status = await self.get_plug_status(name, plug_data)
            plugs_status.append(plug_status)

        # Get all servers status
        servers = self.config.list_servers()
        for name, server_data in servers.items():
            server_status = await self.get_server_status(name, server_data)
            servers_status.append(server_status)

        # Calculate summary
        summary = {
            "servers_online": sum(1 for s in servers_status if s["online"]),
            "servers_total": len(servers_status),
            "plugs_online": sum(1 for p in plugs_status if p.get("online", False)),
            "plugs_on": sum(1 for p in plugs_status if p.get("state") == "on"),
            "plugs_total": len(plugs_status),
            "total_power": sum(p.get("current_power", 0) for p in plugs_status),
        }

        return {
            "summary": summary,
            "servers": servers_status,
            "plugs": plugs_status,
            "timestamp": datetime.utcnow().isoformat(),
        }
