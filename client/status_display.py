#!/usr/bin/env python3
"""
Status Display Module - Handles adaptive terminal display for homelab status
"""
import os
import shutil
from typing import Dict, Optional, List


class StatusDisplay:
    """Handles adaptive status display for different terminal sizes"""
    
    def __init__(self):
        self.min_width = 50
        self.min_height = 10
    
    def get_terminal_size(self) -> tuple:
        """Get current terminal size (columns, rows)"""
        try:
            size = shutil.get_terminal_size(fallback=(80, 24))
            return (size.columns, size.lines)
        except Exception:
            return (80, 24)
    
    def _truncate_text(self, text: str, max_width: int) -> str:
        """Truncate text to fit width"""
        if len(text) <= max_width:
            return text
        return text[:max_width - 3] + "..."
    
    def _format_server_section(self, server: Dict, width: int, show_costs: bool) -> List[str]:
        """Format server information adaptively"""
        lines = []
        status_icon = "🟢" if server["online"] else "🔴"
        
        # Compact mode for narrow terminals
        if width < 70:
            name_line = f"  {status_icon} {server['name']}"
            lines.append(self._truncate_text(name_line, width))
            
            if server["online"] and server.get("uptime"):
                lines.append(self._truncate_text(f"     Up: {server['uptime']}", width))
            elif not server["online"] and server.get("downtime"):
                lines.append(self._truncate_text(f"     Down: {server['downtime']}", width))
            
            if server.get("power"):
                power = server["power"]
                if show_costs and power.get('current_cost_per_hour', 0) > 0:
                    lines.append(self._truncate_text(f"     {power['current']}W ({power['current_cost_per_hour']}€/h)", width))
                else:
                    lines.append(self._truncate_text(f"     {power['current']}W", width))
        else:
            # Full mode for wider terminals
            lines.append("")
            lines.append(self._truncate_text(f"  {status_icon} {server['name']}", width))
            lines.append(self._truncate_text(f"     Hostname: {server['hostname']}", width))
            lines.append(self._truncate_text(f"     IP: {server['ip']}", width))
            
            if server["online"] and server.get("uptime"):
                lines.append(self._truncate_text(f"     Uptime: {server['uptime']}", width))
            elif not server["online"] and server.get("downtime"):
                lines.append(self._truncate_text(f"     Downtime: {server['downtime']}", width))
            
            if server.get("power"):
                power = server["power"]
                power_line = f"     Power: {power['current']}W"
                if show_costs and power.get('current_cost_per_hour', 0) > 0:
                    power_line += f" ({power['current_cost_per_hour']}€/h)"
                lines.append(self._truncate_text(power_line, width))
                
                energy_line = f"     Today: {power['today_energy']}Wh"
                if show_costs and power.get('today_cost', 0) > 0:
                    energy_line += f" ({power['today_cost']}€)"
                lines.append(self._truncate_text(energy_line, width))
                
                month_line = f"     Month: {power['month_energy']}Wh"
                if show_costs and power.get('month_cost', 0) > 0:
                    month_line += f" ({power['month_cost']}€)"
                lines.append(self._truncate_text(month_line, width))
        
        return lines
    
    def _format_plug_section(self, plug: Dict, width: int, show_costs: bool) -> List[str]:
        """Format plug information adaptively"""
        lines = []
        
        if not plug.get("online"):
            lines.append("")
            lines.append(self._truncate_text(f"  ❌ {plug['name']} - OFFLINE", width))
            return lines
        
        state_icon = "⚡" if plug["state"] == "on" else "⭕"
        
        # Compact mode for narrow terminals
        if width < 70:
            name_line = f"  {state_icon} {plug['name']}"
            lines.append(self._truncate_text(name_line, width))
            lines.append(self._truncate_text(f"     {plug['state'].upper()}", width))
            
            if show_costs and plug.get('current_cost_per_hour', 0) > 0:
                lines.append(self._truncate_text(f"     {plug['current_power']}W ({plug['current_cost_per_hour']}€/h)", width))
            else:
                lines.append(self._truncate_text(f"     {plug['current_power']}W", width))
        else:
            # Full mode for wider terminals
            lines.append("")
            lines.append(self._truncate_text(f"  {state_icon} {plug['name']} ({plug['ip']})", width))
            lines.append(self._truncate_text(f"     State: {plug['state'].upper()}", width))
            
            current_line = f"     Current: {plug['current_power']}W"
            if show_costs and plug.get('current_cost_per_hour', 0) > 0:
                current_line += f" ({plug['current_cost_per_hour']}€/h)"
            lines.append(self._truncate_text(current_line, width))
            
            today_line = f"     Today: {plug['today_energy']}Wh ({plug['today_runtime']}h)"
            if show_costs and plug.get('today_cost', 0) > 0:
                today_line += f" - {plug['today_cost']}€"
            lines.append(self._truncate_text(today_line, width))
            
            month_line = f"     Month: {plug['month_energy']}Wh ({plug['month_runtime']}h)"
            if show_costs and plug.get('month_cost', 0) > 0:
                month_line += f" - {plug['month_cost']}€"
            lines.append(self._truncate_text(month_line, width))
        
        return lines
    
    def format_status_output(self, status: dict, timestamp: str, follow_interval: Optional[float]) -> List[str]:
        """Format status data into lines for display, adaptive to terminal size"""
        width, height = self.get_terminal_size()
        
        # Adjust width for content (account for padding)
        content_width = min(width - 2, 100)
        
        lines = []
        summary = status["summary"]
        
        # Determine if we should show costs
        show_costs = any(
            plug.get('current_cost_per_hour', 0) > 0 
            for plug in status.get("plugs", []) 
            if plug.get("online")
        )
        
        # Header
        lines.append("=" * content_width)
        lines.append(" HOMELAB STATUS".center(content_width))
        if follow_interval is not None:
            lines.append(f" Updated: {timestamp} (refresh: {follow_interval}s)".center(content_width))
        lines.append("=" * content_width)
        lines.append("")
        
        # Summary
        lines.append("📊 Summary:")
        lines.append(f"   Servers: {summary['servers_online']}/{summary['servers_total']} online")
        lines.append(f"   Plugs:   {summary['plugs_on']}/{summary['plugs_total']} on ({summary['plugs_online']} reachable)")
        lines.append(f"   Power:   {summary['total_power']:.1f}W total")
        
        # Calculate how many lines we have for content
        header_lines = len(lines)
        footer_lines = 3 if follow_interval else 2  # separator + optional exit message
        available_lines = height - header_lines - footer_lines
        
        # Servers section (limit items if needed)
        if status["servers"]:
            lines.append("")
            lines.append("🖥️  Servers:")
            lines.append("-" * content_width)
            
            servers_to_show = status["servers"]
            if available_lines < 20:  # Very limited space
                # Show only online servers or first 2
                servers_to_show = [s for s in status["servers"] if s["online"]][:2]
                if not servers_to_show:
                    servers_to_show = status["servers"][:2]
            
            for server in servers_to_show:
                server_lines = self._format_server_section(server, content_width, show_costs)
                lines.extend(server_lines)
            
            if len(servers_to_show) < len(status["servers"]):
                lines.append(f"  ... and {len(status['servers']) - len(servers_to_show)} more")
        
        # Plugs section (limit items if needed)
        if status["plugs"]:
            lines.append("")
            lines.append("🔌 Plugs:")
            lines.append("-" * content_width)
            
            plugs_to_show = status["plugs"]
            if available_lines < 20:  # Very limited space
                # Show only online plugs or first 2
                plugs_to_show = [p for p in status["plugs"] if p.get("online")][:2]
                if not plugs_to_show:
                    plugs_to_show = status["plugs"][:2]
            
            for plug in plugs_to_show:
                plug_lines = self._format_plug_section(plug, content_width, show_costs)
                lines.extend(plug_lines)
            
            if len(plugs_to_show) < len(status["plugs"]):
                lines.append(f"  ... and {len(status['plugs']) - len(plugs_to_show)} more")
        
        # Footer
        lines.append("")
        lines.append("=" * content_width)
        
        if follow_interval is not None:
            lines.append("")
            lines.append("Press 'q' or Ctrl+C to exit...")
        
        # Truncate if we still have too many lines
        if len(lines) > height - 1:
            lines = lines[:height - 2]
            lines.append("  ... (terminal too small, resize for full view)")
        
        return lines
