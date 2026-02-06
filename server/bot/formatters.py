from typing import Dict, Optional

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
