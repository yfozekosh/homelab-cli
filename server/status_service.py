"""
Status Service - Aggregates status information for all devices
"""

import logging
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict
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
            now = datetime.now(timezone.utc)
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
        t0 = time.monotonic()
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

            elapsed = time.monotonic() - t0
            logger.debug(
                "get_plug_status %s: done in %.2fs (power=%.1fW, on=%s)",
                name, elapsed, status["current_power"], status["on"],
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
                # Previous day/month values if device or datastore provides them
                "prev_day_energy": status.get("prev_day_energy"),
                "prev_day_cost": round(status.get("prev_day_cost", 0), 4) if status.get("prev_day_cost") is not None else None,
                "prev_month_energy": status.get("prev_month_energy"),
                "prev_month_cost": round(status.get("prev_month_cost", 0), 4) if status.get("prev_month_cost") is not None else None,
            }
        except Exception as e:
            elapsed = time.monotonic() - t0
            logger.error("get_plug_status %s: failed after %.2fs: %s", name, elapsed, e)
            return {
                "name": name,
                "ip": plug_data["ip"],
                "online": False,
                "error": str(e),
            }

    async def get_server_status(self, name: str, server_data: Dict) -> Dict:
        """Get detailed status for a single server"""
        t0 = time.monotonic()

        # Check if server is online and resolve hostname in parallel
        online, ip = await asyncio.gather(
            self.server_service.ping_async(server_data["hostname"]),
            self.server_service.resolve_hostname_async(server_data["hostname"]),
        )

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
            "ip": ip,
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
                        # Previous day/month if available
                        "prev_day_energy": plug_status.get("prev_day_energy"),
                        "prev_day_cost": round(plug_status.get("prev_day_cost", 0), 4) if plug_status.get("prev_day_cost") is not None else None,
                        "prev_month_energy": plug_status.get("prev_month_energy"),
                        "prev_month_cost": round(plug_status.get("prev_month_cost", 0), 4) if plug_status.get("prev_month_cost") is not None else None,
                        "month_runtime": plug_status.get("month_runtime", 0),  # Add runtime in minutes
                    }
                except Exception as e:
                    logger.warning(f"Failed to get power info for {name}: {e}")

        elapsed = time.monotonic() - t0
        logger.debug(
            "get_server_status %s: done in %.2fs (online=%s, ip=%s)",
            name, elapsed, online, ip,
        )

        return result

    async def get_all_status(self) -> Dict:
        """Get comprehensive status of all servers and plugs"""
        t_start = time.monotonic()

        # Get all plugs and servers config
        plugs = self.config.list_plugs()
        servers = self.config.list_servers()

        logger.info(
            "get_all_status: checking %d plugs + %d servers in parallel",
            len(plugs), len(servers),
        )

        # Check all plugs and servers in parallel
        plug_tasks = [
            self.get_plug_status(name, plug_data)
            for name, plug_data in plugs.items()
        ]
        server_tasks = [
            self.get_server_status(name, server_data)
            for name, server_data in servers.items()
        ]

        all_tasks = plug_tasks + server_tasks
        results = await asyncio.gather(*all_tasks, return_exceptions=True)

        # Split results back into plugs and servers
        plugs_count = len(plug_tasks)
        plugs_status = []
        servers_status = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                target = list(plugs.keys())[i] if i < plugs_count else list(servers.keys())[i - plugs_count]
                logger.error("Status check failed for %s: %s", target, result)
                continue
            if i < plugs_count:
                plugs_status.append(result)
            else:
                servers_status.append(result)

        elapsed = time.monotonic() - t_start
        plugs_online = sum(1 for p in plugs_status if p.get("online", False))
        servers_online = sum(1 for s in servers_status if s["online"])
        total_power = sum(p.get("current_power", 0) for p in plugs_status)
        logger.info(
            "get_all_status: done in %.2fs — %d/%d servers online, %d/%d plugs online, %.1fW total",
            elapsed, servers_online, len(servers_status),
            plugs_online, len(plugs_status), total_power,
        )

        # Calculate summary
        summary = {
            "servers_online": servers_online,
            "servers_total": len(servers_status),
            "plugs_online": plugs_online,
            "plugs_on": sum(1 for p in plugs_status if p.get("state") == "on"),
            "plugs_total": len(plugs_status),
            "total_power": total_power,
        }

        return {
            "summary": summary,
            "servers": servers_status,
            "plugs": plugs_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
