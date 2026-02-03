#!/usr/bin/env python3
"""
Status Display Module - Handles adaptive terminal display for homelab status
"""

import os
from typing import Dict, Optional, List


class StatusDisplay:
    """Handles adaptive status display for different terminal sizes"""

    def __init__(self):
        self.min_width = 50
        self.min_height = 10

        # ANSI color codes
        self.COLORS = {
            "RESET": "\033[0m",
            "BOLD": "\033[1m",
            "GREEN": "\033[92m",
            "RED": "\033[91m",
            "YELLOW": "\033[93m",
            "BLUE": "\033[94m",
            "CYAN": "\033[96m",
            "MAGENTA": "\033[95m",
            "GRAY": "\033[90m",
        }

    def _c(self, color: str, text: str, use_color: bool = True) -> str:
        """Apply color to text if colors are enabled"""
        if not use_color:
            return text
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['RESET']}"

    def _format_server_section(
        self, server: Dict, width: int, show_costs: bool, use_color: bool = True
    ) -> List[str]:
        """Format server information adaptively"""
        lines = []
        status_icon = "🟢" if server["online"] else "🔴"
        name_color = "GREEN" if server["online"] else "RED"

        # Compact mode for narrow terminals
        if width < 70:
            name_line = (
                f"  {status_icon} {self._c(name_color, server['name'], use_color)}"
            )
            lines.append(name_line)

            if server["online"] and server.get("uptime"):
                lines.append(f"     Up: {server['uptime']}")
            elif not server["online"] and server.get("downtime"):
                lines.append(f"     Down: {server['downtime']}")

            if server.get("power"):
                power = server["power"]
                if show_costs and power.get("current_cost_per_hour", 0) > 0:
                    lines.append(
                        f"     {power['current']}W ({power['current_cost_per_hour']}€/h)"
                    )
                else:
                    lines.append(f"     {power['current']}W")
        else:
            # Full mode for wider terminals
            lines.append("")
            lines.append(
                f"  {status_icon} {self._c(name_color, server['name'], use_color)}"
            )
            lines.append(
                f"     Hostname: {self._c('CYAN', server['hostname'], use_color)}"
            )
            lines.append(f"     IP: {self._c('CYAN', server['ip'], use_color)}")

            if server["online"] and server.get("uptime"):
                lines.append(f"     Uptime: {server['uptime']}")
            elif not server["online"] and server.get("downtime"):
                lines.append(f"     Downtime: {server['downtime']}")

            if server.get("power"):
                power = server["power"]
                power_w = f"{power['current']}W"
                power_line = f"     Power: {self._c('YELLOW', power_w, use_color)}"
                if show_costs and power.get("current_cost_per_hour", 0) > 0:
                    cost_h = f"{power['current_cost_per_hour']}€/h"
                    power_line += f" ({self._c('MAGENTA', cost_h, use_color)})"
                lines.append(power_line)

                energy_wh = f"{power['today_energy']}Wh"
                energy_line = f"     Today: {self._c('YELLOW', energy_wh, use_color)}"
                if show_costs and power.get("today_cost", 0) > 0:
                    cost = f"{power['today_cost']}€"
                    energy_line += f" ({self._c('MAGENTA', cost, use_color)})"
                lines.append(energy_line)

                month_wh = f"{power['month_energy']}Wh"
                month_line = f"     Month: {self._c('YELLOW', month_wh, use_color)}"
                if show_costs and power.get("month_cost", 0) > 0:
                    cost = f"{power['month_cost']}€"
                    month_line += f" ({self._c('MAGENTA', cost, use_color)})"
                lines.append(month_line)

        return lines

    def _format_plug_section(
        self, plug: Dict, width: int, show_costs: bool, use_color: bool = True
    ) -> List[str]:
        """Format plug information adaptively"""
        lines = []

        if not plug.get("online"):
            lines.append("")
            offline_text = f"{plug['name']} - OFFLINE"
            lines.append(f"  ❌ {self._c('RED', offline_text, use_color)}")
            return lines

        state_icon = "⚡" if plug["state"] == "on" else "⭕"
        state_color = "GREEN" if plug["state"] == "on" else "GRAY"

        # Compact mode for narrow terminals
        if width < 70:
            name_line = (
                f"  {state_icon} {self._c(state_color, plug['name'], use_color)}"
            )
            lines.append(name_line)
            lines.append(
                f"     {self._c(state_color, plug['state'].upper(), use_color)}"
            )

            if show_costs and plug.get("current_cost_per_hour", 0) > 0:
                lines.append(
                    f"     {plug['current_power']}W ({plug['current_cost_per_hour']}€/h)"
                )
            else:
                lines.append(f"     {plug['current_power']}W")
        else:
            # Full mode for wider terminals
            lines.append("")
            lines.append(
                f"  {state_icon} {self._c(state_color, plug['name'], use_color)} ({self._c('CYAN', plug['ip'], use_color)})"
            )
            lines.append(
                f"     State: {self._c(state_color, plug['state'].upper(), use_color)}"
            )

            current_w = f"{plug['current_power']}W"
            current_line = f"     Current: {self._c('YELLOW', current_w, use_color)}"
            if show_costs and plug.get("current_cost_per_hour", 0) > 0:
                cost_h = f"{plug['current_cost_per_hour']}€/h"
                current_line += f" ({self._c('MAGENTA', cost_h, use_color)})"
            lines.append(current_line)

            energy_wh = f"{plug['today_energy']}Wh"
            today_line = f"     Today: {self._c('YELLOW', energy_wh, use_color)} ({plug['today_runtime']}h)"
            if show_costs and plug.get("today_cost", 0) > 0:
                cost = f"{plug['today_cost']}€"
                today_line += f" - {self._c('MAGENTA', cost, use_color)}"
            lines.append(today_line)

            month_wh = f"{plug['month_energy']}Wh"
            month_line = f"     Month: {self._c('YELLOW', month_wh, use_color)} ({plug['month_runtime']}h)"
            if show_costs and plug.get("month_cost", 0) > 0:
                cost = f"{plug['month_cost']}€"
                month_line += f" - {self._c('MAGENTA', cost, use_color)}"
            lines.append(month_line)

        return lines

    def format_status_output(
        self,
        status: dict,
        timestamp: str,
        follow_interval: Optional[float],
        use_color: bool = True,
    ) -> List[str]:
        """Format status data into lines for display, adaptive to terminal size"""

        content_width = max(self.min_width, os.get_terminal_size().columns)
        height = max(self.min_height, os.get_terminal_size().lines)

        lines = []
        summary = status["summary"]

        # Determine if we should show costs
        show_costs = any(
            plug.get("current_cost_per_hour", 0) > 0
            for plug in status.get("plugs", [])
            if plug.get("online")
        )

        # Header
        lines.append(self._c("BOLD", "=" * content_width, use_color))
        lines.append(
            self._c("BOLD", " HOMELAB STATUS".center(content_width), use_color)
        )
        if follow_interval is not None:
            lines.append(
                self._c(
                    "GRAY",
                    f" Updated: {timestamp} (refresh: {follow_interval}s)".center(
                        content_width
                    ),
                    use_color,
                )
            )
        lines.append(self._c("BOLD", "=" * content_width, use_color))
        lines.append("")

        # Summary
        lines.append(self._c("BOLD", "📊 Summary:", use_color))
        servers_ratio = f"{summary['servers_online']}/{summary['servers_total']}"
        lines.append(f"   Servers: {self._c('GREEN', servers_ratio, use_color)} online")
        plugs_ratio = f"{summary['plugs_on']}/{summary['plugs_total']}"
        lines.append(
            f"   Plugs:   {self._c('GREEN', plugs_ratio, use_color)} on ({summary['plugs_online']} reachable)"
        )
        power_total = f"{summary['total_power']:.1f}W"
        lines.append(f"   Power:   {self._c('YELLOW', power_total, use_color)} total")

        # Projections based on current power usage
        current_power_w = summary["total_power"]

        # Get price per kWh if costs are being shown
        price_per_kwh = None
        if show_costs:
            for plug in status.get("plugs", []):
                if plug.get("online") and plug.get("current_cost_per_hour", 0) > 0:
                    if plug.get("current_power", 0) > 0:
                        cost_per_hour = plug["current_cost_per_hour"]
                        power_w = plug["current_power"]
                        price_per_kwh = (cost_per_hour * 1000) / power_w
                        break

        # 12h projection
        half_day_energy_kwh = (current_power_w * 12) / 1000
        energy_12h = f"{half_day_energy_kwh:.2f}kWh"
        projection_12h = (
            f"   12h:     {self._c('CYAN', energy_12h, use_color)} projected"
        )
        if price_per_kwh:
            half_day_cost = half_day_energy_kwh * price_per_kwh
            cost_12h = f"{half_day_cost:.2f}€"
            projection_12h += f" ({self._c('MAGENTA', cost_12h, use_color)})"
        lines.append(projection_12h)

        # Daily projection
        daily_energy_kwh = (current_power_w * 24) / 1000
        energy_daily = f"{daily_energy_kwh:.2f}kWh"
        projection_daily = (
            f"   Daily:   {self._c('CYAN', energy_daily, use_color)} projected"
        )
        if price_per_kwh:
            daily_cost = daily_energy_kwh * price_per_kwh
            cost_daily = f"{daily_cost:.2f}€"
            projection_daily += f" ({self._c('MAGENTA', cost_daily, use_color)})"
        lines.append(projection_daily)

        # Monthly projection (30 days)
        monthly_energy_kwh = (current_power_w * 24 * 30) / 1000
        energy_monthly = f"{monthly_energy_kwh:.2f}kWh"
        projection_monthly = (
            f"   Monthly: {self._c('CYAN', energy_monthly, use_color)} projected"
        )
        if price_per_kwh:
            monthly_cost = monthly_energy_kwh * price_per_kwh
            cost_monthly = f"{monthly_cost:.2f}€"
            projection_monthly += f" ({self._c('MAGENTA', cost_monthly, use_color)})"
        lines.append(projection_monthly)

        # Calculate how many lines we have for content
        header_lines = len(lines)
        footer_lines = 3 if follow_interval else 2  # separator + optional exit message
        available_lines = height - header_lines - footer_lines

        # Servers section (limit items if needed)
        if status["servers"]:
            lines.append("")
            lines.append(self._c("BOLD", "🖥️  Servers:", use_color))
            lines.append(self._c("GRAY", "-" * content_width, use_color))

            servers_to_show = status["servers"]
            if available_lines < 20:  # Very limited space
                # Show only online servers or first 2
                servers_to_show = [s for s in status["servers"] if s["online"]][:2]
                if not servers_to_show:
                    servers_to_show = status["servers"][:2]

            for server in servers_to_show:
                server_lines = self._format_server_section(
                    server, content_width, show_costs, use_color
                )
                lines.extend(server_lines)

            if len(servers_to_show) < len(status["servers"]):
                lines.append(
                    f"  ... and {len(status['servers']) - len(servers_to_show)} more"
                )

        # Plugs section (limit items if needed)
        if status["plugs"]:
            lines.append("")
            lines.append(self._c("BOLD", "🔌 Plugs:", use_color))
            lines.append(self._c("GRAY", "-" * content_width, use_color))

            plugs_to_show = status["plugs"]
            if available_lines < 20:  # Very limited space
                # Show only online plugs or first 2
                plugs_to_show = [p for p in status["plugs"] if p.get("online")][:2]
                if not plugs_to_show:
                    plugs_to_show = status["plugs"][:2]

            for plug in plugs_to_show:
                plug_lines = self._format_plug_section(
                    plug, content_width, show_costs, use_color
                )
                lines.extend(plug_lines)

            if len(plugs_to_show) < len(status["plugs"]):
                lines.append(
                    f"  ... and {len(status['plugs']) - len(plugs_to_show)} more"
                )

        # Footer
        lines.append("")
        lines.append(self._c("BOLD", "=" * content_width, use_color))

        if follow_interval is not None:
            lines.append("")
            footer_text = "Use arrow keys or j/k to scroll, 'q' to exit"
            lines.append(self._c("GRAY", footer_text, use_color))

        return lines
