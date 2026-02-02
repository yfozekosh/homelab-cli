#!/usr/bin/env python3
"""
Homelab CLI Client - Lightweight client for homelab server
"""
import sys
import os
import json
import argparse
import time
import select
import threading
from pathlib import Path
from typing import Optional
import requests


class HomelabClient:
    """Client for Homelab API"""

    def __init__(self, server_url: Optional[str] = None, api_key: Optional[str] = None):
        self.config_dir = Path.home() / ".config" / "homelab-client"
        self.config_file = self.config_dir / "config.json"
        
        # Load or set configuration
        config = self._load_config()
        self.server_url = server_url or config.get("server_url") or os.getenv("HOMELAB_SERVER_URL")
        self.api_key = api_key or config.get("api_key") or os.getenv("HOMELAB_API_KEY")
        
        if not self.server_url:
            print("❌ Error: Server URL not configured.")
            print("Set HOMELAB_SERVER_URL environment variable or run: lab config set-server <url>")
            sys.exit(1)
        
        if not self.api_key:
            print("❌ Error: API key not configured.")
            print("Set HOMELAB_API_KEY environment variable or run: lab config set-key <key>")
            sys.exit(1)
        
        self.headers = {"X-API-Key": self.api_key}

    def _load_config(self) -> dict:
        """Load client configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_config(self, config: dict):
        """Save client configuration"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def health_check(self) -> bool:
        """Check server health"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def list_plugs(self):
        """List all plugs"""
        try:
            response = requests.get(
                f"{self.server_url}/plugs",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            plugs = response.json()["plugs"]
            
            if not plugs:
                print("No plugs configured")
                return
            
            print("\nConfigured Plugs:")
            print("-" * 40)
            for idx, (name, data) in enumerate(plugs.items(), 1):
                print(f"{idx}. {name}")
                print(f"   IP: {data['ip']}")
            print()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def list_servers(self):
        """List all servers"""
        try:
            response = requests.get(
                f"{self.server_url}/servers",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            servers = response.json()["servers"]
            
            if not servers:
                print("No servers configured")
                return
            
            print("\nConfigured Servers:")
            print("-" * 60)
            for idx, (name, data) in enumerate(servers.items(), 1):
                status = "🟢 Online" if data.get("online") else "🔴 Offline"
                print(f"{idx}. {name} - {status}")
                print(f"   Hostname: {data['hostname']}")
                print(f"   MAC: {data['mac']}")
                print(f"   Plug: {data.get('plug', 'None')}")
                print(f"   IP: {data.get('ip', 'Unknown')}")
                print()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def add_plug(self, name: str, ip: str):
        """Add a plug"""
        try:
            response = requests.post(
                f"{self.server_url}/plugs",
                headers=self.headers,
                json={"name": name, "ip": ip},
                timeout=10
            )
            response.raise_for_status()
            print(f"✓ Plug '{name}' added successfully")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def remove_plug(self, name: str):
        """Remove a plug"""
        try:
            response = requests.delete(
                f"{self.server_url}/plugs",
                headers=self.headers,
                json={"name": name},
                timeout=10
            )
            response.raise_for_status()
            print(f"✓ Plug '{name}' removed successfully")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def add_server(self, name: str, hostname: str, mac: Optional[str] = None, plug: Optional[str] = None):
        """Add a server"""
        try:
            response = requests.post(
                f"{self.server_url}/servers",
                headers=self.headers,
                json={"name": name, "hostname": hostname, "mac": mac, "plug": plug},
                timeout=10
            )
            response.raise_for_status()
            print(f"✓ Server '{name}' added successfully")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def edit_server(self, name: str, hostname: Optional[str] = None, mac: Optional[str] = None, plug: Optional[str] = None):
        """Edit server configuration"""
        try:
            data = {"name": name}
            if hostname is not None:
                data["hostname"] = hostname
            if mac is not None:
                data["mac"] = mac
            if plug is not None:
                data["plug"] = plug
            
            response = requests.put(
                f"{self.server_url}/servers",
                headers=self.headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            print(f"✓ Server '{name}' updated successfully")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def edit_plug(self, name: str, ip: str):
        """Edit plug IP address"""
        try:
            response = requests.put(
                f"{self.server_url}/plugs",
                headers=self.headers,
                json={"name": name, "ip": ip},
                timeout=10
            )
            response.raise_for_status()
            print(f"✓ Plug '{name}' updated successfully")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def remove_server(self, name: str):
        """Remove a server"""
        try:
            response = requests.delete(
                f"{self.server_url}/servers",
                headers=self.headers,
                json={"name": name},
                timeout=10
            )
            response.raise_for_status()
            print(f"✓ Server '{name}' removed successfully")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def power_on(self, name: str):
        """Power on a server"""
        print(f"⚡ Powering on server '{name}'...")
        try:
            response = requests.post(
                f"{self.server_url}/power/on",
                headers=self.headers,
                json={"name": name},
                timeout=180
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                print(f"✓ Server '{name}' powered on successfully")
                if result.get("logs"):
                    print("\nLogs:")
                    for log in result["logs"][-5:]:  # Show last 5 logs
                        print(f"  {log}")
            else:
                print(f"❌ Failed: {result.get('message')}")
                sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def power_off(self, name: str):
        """Power off a server"""
        print(f"🔴 Powering off server '{name}'...")
        try:
            response = requests.post(
                f"{self.server_url}/power/off",
                headers=self.headers,
                json={"name": name},
                timeout=180
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                print(f"✓ Server '{name}' powered off successfully")
                if result.get("logs"):
                    print("\nLogs:")
                    for log in result["logs"][-5:]:
                        print(f"  {log}")
            else:
                print(f"⚠️  {result.get('message')}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def set_electricity_price(self, price: float):
        """Set electricity price per kWh"""
        try:
            response = requests.post(
                f"{self.server_url}/settings/electricity-price",
                headers=self.headers,
                json={"price": price},
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            print(f"✓ Electricity price set to {price} per kWh")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    def get_electricity_price(self):
        """Get current electricity price"""
        try:
            response = requests.get(
                f"{self.server_url}/settings/electricity-price",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            price = result.get("price", 0.0)
            if price > 0:
                print(f"💰 Current electricity price: {price} per kWh")
            else:
                print(f"💰 No electricity price set (set with: lab set price <value>)")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def _format_status_output(self, status: dict, timestamp: str, follow_interval: Optional[float]) -> list:
        """Format status data into lines for display"""
        lines = []
        summary = status["summary"]
        
        lines.append("=" * 70)
        lines.append(" HOMELAB STATUS".center(70))
        if follow_interval is not None:
            lines.append(f" Updated: {timestamp} (refresh: {follow_interval}s)".center(70))
        lines.append("=" * 70)
        lines.append("")
        lines.append("📊 Summary:")
        lines.append(f"   Servers: {summary['servers_online']}/{summary['servers_total']} online")
        lines.append(f"   Plugs:   {summary['plugs_on']}/{summary['plugs_total']} on ({summary['plugs_online']} reachable)")
        lines.append(f"   Power:   {summary['total_power']:.1f}W total")
        
        # Servers section
        if status["servers"]:
            lines.append("")
            lines.append("🖥️  Servers:")
            lines.append("-" * 70)
            for server in status["servers"]:
                status_icon = "🟢" if server["online"] else "🔴"
                lines.append("")
                lines.append(f"  {status_icon} {server['name']}")
                lines.append(f"     Hostname: {server['hostname']}")
                lines.append(f"     IP: {server['ip']}")
                
                if server["online"] and server.get("uptime"):
                    lines.append(f"     Uptime: {server['uptime']}")
                elif not server["online"] and server.get("downtime"):
                    lines.append(f"     Downtime: {server['downtime']}")
                
                if server.get("power"):
                    power = server["power"]
                    power_line = f"     Power: {power['current']}W"
                    if power.get('current_cost_per_hour', 0) > 0:
                        power_line += f" ({power['current_cost_per_hour']}€/h)"
                    lines.append(power_line)
                    
                    energy_line = f"     Today: {power['today_energy']}Wh"
                    if power.get('today_cost', 0) > 0:
                        energy_line += f" ({power['today_cost']}€)"
                    lines.append(energy_line)
                    
                    month_line = f"     Month: {power['month_energy']}Wh"
                    if power.get('month_cost', 0) > 0:
                        month_line += f" ({power['month_cost']}€)"
                    lines.append(month_line)
        
        # Plugs section
        if status["plugs"]:
            lines.append("")
            lines.append("🔌 Plugs:")
            lines.append("-" * 70)
            for plug in status["plugs"]:
                if plug.get("online"):
                    state_icon = "⚡" if plug["state"] == "on" else "⭕"
                    lines.append("")
                    lines.append(f"  {state_icon} {plug['name']} ({plug['ip']})")
                    lines.append(f"     State: {plug['state'].upper()}")
                    
                    current_line = f"     Current: {plug['current_power']}W"
                    if plug.get('current_cost_per_hour', 0) > 0:
                        current_line += f" ({plug['current_cost_per_hour']}€/h)"
                    lines.append(current_line)
                    
                    today_line = f"     Today: {plug['today_energy']}Wh ({plug['today_runtime']}h)"
                    if plug.get('today_cost', 0) > 0:
                        today_line += f" - {plug['today_cost']}€"
                    lines.append(today_line)
                    
                    month_line = f"     Month: {plug['month_energy']}Wh ({plug['month_runtime']}h)"
                    if plug.get('month_cost', 0) > 0:
                        month_line += f" - {plug['month_cost']}€"
                    lines.append(month_line)
                else:
                    lines.append("")
                    lines.append(f"  ❌ {plug['name']} ({plug['ip']}) - OFFLINE")
        
        lines.append("")
        lines.append("=" * 70)
        
        if follow_interval is not None:
            lines.append("")
            lines.append("Press 'q' or Ctrl+C to exit...")
        
        return lines

    def _wait_for_input(self, interval: float, stop_event: threading.Event) -> bool:
        """Wait for interval or keyboard input
        
        Args:
            interval: Time to wait in seconds
            stop_event: Event to signal early exit
            
        Returns:
            True if should continue, False if should exit
        """
        start_time = time.time()
        
        while time.time() - start_time < interval:
            if stop_event.is_set():
                return False
            
            # Check for keyboard input (Unix-like systems)
            if os.name != 'nt':  # Unix/Linux/macOS
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1)
                    if char.lower() == 'q':
                        return False
            else:  # Windows
                # On Windows, use msvcrt if available
                try:
                    import msvcrt
                    if msvcrt.kbhit():
                        char = msvcrt.getch().decode('utf-8', errors='ignore')
                        if char.lower() == 'q':
                            return False
                except ImportError:
                    pass
            
            time.sleep(0.1)
        
        return True

    def get_status(self, follow_interval: Optional[float] = None):
        """Get comprehensive status of all servers and plugs
        
        Args:
            follow_interval: If provided, continuously update at this interval (in seconds)
        """
        prev_lines = []
        stop_event = threading.Event()
        
        # Set terminal to raw mode for non-blocking input (Unix only)
        old_settings = None
        if follow_interval is not None and os.name != 'nt':
            try:
                import tty
                import termios
                old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())
            except (ImportError, OSError):
                pass
        
        try:
            first_run = True
            while True:
                response = requests.get(
                    f"{self.server_url}/status",
                    headers=self.headers,
                    timeout=30
                )
                response.raise_for_status()
                status = response.json()
                
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                current_lines = self._format_status_output(status, timestamp, follow_interval)
                
                if follow_interval is not None and not first_run:
                    # Move cursor to beginning and update only changed lines
                    # ANSI codes: \033[H moves to home, \033[K clears to end of line
                    print("\033[H", end="")  # Move cursor to top-left
                    
                    for i, line in enumerate(current_lines):
                        if i >= len(prev_lines) or line != prev_lines[i]:
                            # Clear line and print new content
                            print(f"\033[K{line}")
                        else:
                            # Skip to next line without rewriting
                            print()
                    
                    # Clear any extra lines from previous output
                    if len(prev_lines) > len(current_lines):
                        for _ in range(len(prev_lines) - len(current_lines)):
                            print("\033[K")
                else:
                    # First run or one-time mode: print normally
                    print("\n" + "\n".join(current_lines))
                    if follow_interval is None:
                        print()
                        break
                
                prev_lines = current_lines
                first_run = False
                
                if follow_interval is not None:
                    # Wait for interval or keyboard input
                    if not self._wait_for_input(follow_interval, stop_event):
                        print("\n\n✓ Status monitoring stopped\n")
                        break
            
        except KeyboardInterrupt:
            print("\n\n✓ Status monitoring stopped\n")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
        finally:
            # Restore terminal settings
            if old_settings is not None and os.name != 'nt':
                try:
                    import termios
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                except (ImportError, OSError):
                    pass

    def set_server_url(self, url: str):
        """Set server URL in config"""
        config = self._load_config()
        config["server_url"] = url
        self._save_config(config)
        print(f"✓ Server URL set to: {url}")

    def set_api_key(self, key: str):
        """Set API key in config"""
        config = self._load_config()
        config["api_key"] = key
        self._save_config(config)
        print("✓ API key saved")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Homelab Management CLI Client",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Config commands
    config_parser = subparsers.add_parser("config", help="Configure client")
    config_sub = config_parser.add_subparsers(dest="action")
    
    config_server = config_sub.add_parser("set-server", help="Set server URL")
    config_server.add_argument("url", help="Server URL (e.g., http://localhost:8000)")
    
    config_key = config_sub.add_parser("set-key", help="Set API key")
    config_key.add_argument("key", help="API key")
    
    config_sub.add_parser("test", help="Test connection to server")
    
    # Plug commands
    plug_parser = subparsers.add_parser("plug", help="Manage plugs")
    plug_sub = plug_parser.add_subparsers(dest="action")
    
    plug_add = plug_sub.add_parser("add", help="Add a plug")
    plug_add.add_argument("name", help="Plug name")
    plug_add.add_argument("ip", help="Plug IP address")
    
    plug_edit = plug_sub.add_parser("edit", help="Edit a plug")
    plug_edit.add_argument("name", help="Plug name")
    plug_edit.add_argument("ip", help="New IP address")
    
    plug_remove = plug_sub.add_parser("remove", help="Remove a plug")
    plug_remove.add_argument("name", help="Plug name")
    
    plug_sub.add_parser("list", help="List plugs")
    
    # Server commands
    server_parser = subparsers.add_parser("server", help="Manage servers")
    server_sub = server_parser.add_subparsers(dest="action")
    
    server_add = server_sub.add_parser("add", help="Add a server")
    server_add.add_argument("name", help="Server name")
    server_add.add_argument("hostname", help="Server hostname")
    server_add.add_argument("mac", nargs="?", help="Server MAC address (optional)")
    server_add.add_argument("plug", nargs="?", help="Associated plug name (optional)")
    
    server_edit = server_sub.add_parser("edit", help="Edit a server")
    server_edit.add_argument("name", help="Server name")
    server_edit.add_argument("--hostname", help="New hostname")
    server_edit.add_argument("--mac", help="New MAC address")
    server_edit.add_argument("--plug", help="New plug name")
    
    server_remove = server_sub.add_parser("remove", help="Remove a server")
    server_remove.add_argument("name", help="Server name")
    
    server_sub.add_parser("list", help="List servers")
    
    # Power commands
    on_parser = subparsers.add_parser("on", help="Power on a server")
    on_parser.add_argument("name", help="Server name")
    
    off_parser = subparsers.add_parser("off", help="Power off a server")
    off_parser.add_argument("name", help="Server name")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show status of all servers and plugs")
    status_parser.add_argument("-f", "--follow", nargs="?", const=5.0, type=float, metavar="INTERVAL",
                               help="Continuously update status (default: 5s, e.g., -f 0.5 for 500ms, -f 60 for 1min)")
    
    # Set command (for settings)
    set_parser = subparsers.add_parser("set", help="Set configuration values")
    set_sub = set_parser.add_subparsers(dest='setting', required=True)
    
    price_parser = set_sub.add_parser("price", help="Set electricity price per kWh")
    price_parser.add_argument("value", type=float, help="Price per kWh (e.g., 0.2721)")
    
    # Get command (for settings)
    get_parser = subparsers.add_parser("get", help="Get configuration values")
    get_sub = get_parser.add_subparsers(dest='setting', required=True)
    get_sub.add_parser("price", help="Get current electricity price")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Handle config commands specially (don't need full client init)
    if args.command == "config":
        client = HomelabClient.__new__(HomelabClient)
        client.config_dir = Path.home() / ".config" / "homelab-client"
        client.config_file = client.config_dir / "config.json"
        
        if args.action == "set-server":
            client._save_config = HomelabClient._save_config.__get__(client)
            client._load_config = HomelabClient._load_config.__get__(client)
            client.set_server_url(args.url)
            return
        elif args.action == "set-key":
            client._save_config = HomelabClient._save_config.__get__(client)
            client._load_config = HomelabClient._load_config.__get__(client)
            client.set_api_key(args.key)
            return
        elif args.action == "test":
            # For test, need full client
            pass
    
    # Initialize client
    try:
        client = HomelabClient()
    except SystemExit:
        sys.exit(1)
    
    # Check connection on startup
    if args.command != "config":
        if not client.health_check():
            print("⚠️  Warning: Cannot connect to server")
            print(f"   Server URL: {client.server_url}")
    
    # Handle commands
    try:
        if args.command == "config" and args.action == "test":
            if client.health_check():
                print("✓ Connection successful")
                print(f"  Server URL: {client.server_url}")
            else:
                print("❌ Connection failed")
                print(f"   Server URL: {client.server_url}")
                sys.exit(1)
        
        elif args.command == "plug":
            if args.action == "add":
                client.add_plug(args.name, args.ip)
            elif args.action == "edit":
                client.edit_plug(args.name, args.ip)
            elif args.action == "remove":
                client.remove_plug(args.name)
            elif args.action == "list":
                client.list_plugs()
        
        elif args.command == "server":
            if args.action == "add":
                client.add_server(args.name, args.hostname, args.mac, args.plug)
            elif args.action == "edit":
                if not any([args.hostname, args.mac, args.plug]):
                    print("❌ Error: At least one field must be specified for editing")
                    print("Usage: lab server edit <name> [--hostname HOST] [--mac MAC] [--plug PLUG]")
                    sys.exit(1)
                client.edit_server(args.name, args.hostname, args.mac, args.plug)
            elif args.action == "remove":
                client.remove_server(args.name)
            elif args.action == "list":
                client.list_servers()
        
        elif args.command == "on":
            client.power_on(args.name)
        
        elif args.command == "off":
            client.power_off(args.name)
        
        elif args.command == "status":
            follow_interval = args.follow if hasattr(args, 'follow') and args.follow else None
            client.get_status(follow_interval=follow_interval)
        
        elif args.command == "set":
            if args.setting == "price":
                client.set_electricity_price(args.value)
        
        elif args.command == "get":
            if args.setting == "price":
                client.get_electricity_price()
    
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted")
        sys.exit(1)


if __name__ == "__main__":
    main()
