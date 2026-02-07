from typing import Dict, Optional, List

def format_short_status(status: Dict) -> str:
    """Format short status summary for main menu"""
    summary = status["summary"]
    lines = []
    
    lines.append("📊 *Quick Status:*")
    lines.append(f"  🖥️ Servers: {summary['servers_online']}/{summary['servers_total']} online")
    lines.append(f"  🔌 Plugs: {summary['plugs_on']}/{summary['plugs_total']} on")
    lines.append(f"  ⚡ Power: {summary['total_power']:.1f}W")
    
    return "\n".join(lines)

def format_servers_summary(servers: List[Dict]) -> str:
    """Format servers summary for servers list view"""
    lines = []
    online_count = sum(1 for s in servers if s.get("online", False))
    total_count = len(servers)
    
    lines.append(f"🖥️ *Servers:* {online_count}/{total_count} online")
    
    if servers:
        lines.append("")
        for server in servers:
            status = "🟢" if server.get("online") else "🔴"
            power_info = ""
            if server.get("power"):
                power_info = f" - {server['power']['current']}W"
            lines.append(f"{status} {server['name']}{power_info}")
    
    return "\n".join(lines)

def format_plugs_summary(plugs: List[Dict]) -> str:
    """Format plugs summary for plugs list view"""
    lines = []
    on_count = sum(1 for p in plugs if p.get("state") == "on" and p.get("online"))
    total_count = len(plugs)
    online_count = sum(1 for p in plugs if p.get("online"))
    
    lines.append(f"🔌 *Plugs:* {on_count}/{total_count} on ({online_count} online)")
    
    if plugs:
        lines.append("")
        for plug in plugs:
            if not plug.get("online"):
                lines.append(f"🔴 {plug['name']} - offline")
            else:
                state_icon = "⚡" if plug["state"] == "on" else "⭕"
                power_info = f" - {plug['current_power']}W" if plug.get('current_power') else ""
                lines.append(f"{state_icon} {plug['name']}{power_info}")
    
    return "\n".join(lines)

def format_status_text(status: Dict) -> str:
    """Format full status as Telegram message (CLI-like)"""
    summary = status["summary"]
    lines = []

    lines.append("📊 *HOMELAB STATUS*")
    lines.append("")

    # Summary section
    lines.append("*Summary:*")
    lines.append(f"  Servers: {summary['servers_online']}/{summary['servers_total']} online")
    lines.append(f"  Plugs: {summary['plugs_on']}/{summary['plugs_total']} on ({summary['plugs_online']} reachable)")
    lines.append(f"  Power: {summary['total_power']:.1f}W total")

    # Servers section
    if status["servers"]:
        lines.append("")
        lines.append("*🖥️ Servers:*")
        for server in status["servers"]:
            status_icon = "🟢" if server["online"] else "🔴"
            lines.append(f"\n{status_icon} *{server['name']}*")
            lines.append(f"  Host: `{server['hostname']}` ({server['ip']})")

            if server["online"] and server.get("uptime"):
                lines.append(f"  Uptime: {server['uptime']}")
            elif not server["online"] and server.get("downtime"):
                lines.append(f"  Downtime: {server['downtime']}")

            if server.get("power"):
                power = server["power"]
                power_line = f"  ⚡ {power['current']}W"
                if power.get("current_cost_per_hour", 0) > 0:
                    power_line += f" ({power['current_cost_per_hour']:.4f}€/h)"
                lines.append(power_line)

                lines.append(f"  Today: {power['today_energy']}Wh" +
                            (f" ({power['today_cost']:.2f}€)" if power.get('today_cost', 0) > 0 else ""))
                lines.append(f"  Month: {power['month_energy']}Wh" +
                            (f" ({power['month_cost']:.2f}€)" if power.get('month_cost', 0) > 0 else ""))

    # Plugs section (standalone plugs not attached to servers)
    standalone_plugs = [p for p in status.get("plugs", [])
                      if not any(s.get("plug") == p["name"] for s in status.get("servers", []))]
    if standalone_plugs:
        lines.append("")
        lines.append("*🔌 Plugs:*")
        for plug in standalone_plugs:
            if not plug.get("online"):
                lines.append(f"\n❌ *{plug['name']}* - OFFLINE")
                continue

            state_icon = "⚡" if plug["state"] == "on" else "⭕"
            lines.append(f"\n{state_icon} *{plug['name']}* ({plug['state'].upper()})")
            lines.append(f"  IP: `{plug['ip']}`")

            power_line = f"  Power: {plug['current_power']}W"
            if plug.get("current_cost_per_hour", 0) > 0:
                power_line += f" ({plug['current_cost_per_hour']:.4f}€/h)"
            lines.append(power_line)

            lines.append(f"  Today: {plug['today_energy']}Wh ({plug['today_runtime']}h)" +
                        (f" - {plug['today_cost']:.2f}€" if plug.get('today_cost', 0) > 0 else ""))
            lines.append(f"  Month: {plug['month_energy']}Wh ({plug['month_runtime']}h)" +
                        (f" - {plug['month_cost']:.2f}€" if plug.get('month_cost', 0) > 0 else ""))

    return "\n".join(lines)

def format_server_status_text(server: Dict, plug_status: Optional[Dict] = None) -> str:
    """Format single server status as Telegram message"""
    lines = []
    status_icon = "🟢" if server["online"] else "🔴"
    status_text = "Online" if server["online"] else "Offline"

    lines.append(f"🖥️ *{server['name']}* {status_icon}")
    lines.append("")
    lines.append(f"*Status:* {status_text}")
    lines.append(f"*Hostname:* `{server['hostname']}`")
    lines.append(f"*IP:* `{server['ip']}`")

    if server.get("mac"):
        lines.append(f"*MAC:* `{server['mac']}`")
    if server.get("plug"):
        lines.append(f"*Plug:* {server['plug']}")

    if server["online"] and server.get("uptime"):
        lines.append(f"*Uptime:* {server['uptime']}")
    elif not server["online"] and server.get("downtime"):
        lines.append(f"*Downtime:* {server['downtime']}")

    if server.get("power"):
        power = server["power"]
        lines.append("")
        lines.append("*⚡ Power:*")
        power_line = f"  Current: {power['current']}W"
        if power.get("current_cost_per_hour", 0) > 0:
            power_line += f" ({power['current_cost_per_hour']:.4f}€/h)"
        lines.append(power_line)

        lines.append(f"  Today: {power['today_energy']}Wh" +
                    (f" ({power['today_cost']:.2f}€)" if power.get('today_cost', 0) > 0 else ""))
        lines.append(f"  Month: {power['month_energy']}Wh" +
                    (f" ({power['month_cost']:.2f}€)" if power.get('month_cost', 0) > 0 else ""))

    return "\n".join(lines)


def format_plug_status_text(plug: Dict) -> str:
    """Format single plug status as Telegram message"""
    lines = []
    
    if not plug.get("online"):
        return f"🔌 *{plug['name']}* 🔴\n\n*Status:* Offline\n*IP:* `{plug['ip']}`\n*Error:* {plug.get('error', 'Unknown')}"

    state_icon = "⚡" if plug["state"] == "on" else "⭕"
    state_text = "ON" if plug["state"] == "on" else "OFF"
    
    lines.append(f"🔌 *{plug['name']}* {state_icon}")
    lines.append("")
    lines.append(f"*Status:* {state_text}")
    lines.append(f"*IP:* `{plug['ip']}`")
    
    lines.append("")
    lines.append("*⚡ Power Stats:*")
    
    power_line = f"  Current: {plug['current_power']}W"
    if plug.get("current_cost_per_hour", 0) > 0:
        power_line += f" ({plug['current_cost_per_hour']:.4f}€/h)"
    lines.append(power_line)

    lines.append(f"  Today: {plug['today_energy']}Wh ({plug['today_runtime']}h)" +
                (f" - {plug['today_cost']:.2f}€" if plug.get('today_cost', 0) > 0 else ""))
    
    lines.append(f"  Month: {plug['month_energy']}Wh ({plug['month_runtime']}h)" +
                (f" - {plug['month_cost']:.2f}€" if plug.get('month_cost', 0) > 0 else ""))

    return "\n".join(lines)
