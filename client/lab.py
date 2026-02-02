#!/usr/bin/env python3
"""
Homelab CLI Client - Lightweight client for homelab server
"""
import sys
import os
import json
import argparse
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

    def get_status(self):
        """Get comprehensive status of all servers and plugs"""
        try:
            response = requests.get(
                f"{self.server_url}/status",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            status = response.json()
            
            # Print summary
            summary = status["summary"]
            print("\n" + "=" * 70)
            print(" HOMELAB STATUS".center(70))
            print("=" * 70)
            print(f"\n📊 Summary:")
            print(f"   Servers: {summary['servers_online']}/{summary['servers_total']} online")
            print(f"   Plugs:   {summary['plugs_on']}/{summary['plugs_total']} on ({summary['plugs_online']} reachable)")
            print(f"   Power:   {summary['total_power']:.1f}W total")
            
            # Print servers
            if status["servers"]:
                print(f"\n🖥️  Servers:")
                print("-" * 70)
                for server in status["servers"]:
                    status_icon = "🟢" if server["online"] else "🔴"
                    print(f"\n  {status_icon} {server['name']}")
                    print(f"     Hostname: {server['hostname']}")
                    print(f"     IP: {server['ip']}")
                    
                    if server["online"] and server.get("uptime"):
                        print(f"     Uptime: {server['uptime']}")
                    elif not server["online"] and server.get("downtime"):
                        print(f"     Downtime: {server['downtime']}")
                    
                    if server.get("power"):
                        power = server["power"]
                        print(f"     Power: {power['current']}W (today: {power['today_energy']}Wh, month: {power['month_energy']}Wh)")
            
            # Print plugs
            if status["plugs"]:
                print(f"\n🔌 Plugs:")
                print("-" * 70)
                for plug in status["plugs"]:
                    if plug.get("online"):
                        state_icon = "⚡" if plug["state"] == "on" else "⭕"
                        print(f"\n  {state_icon} {plug['name']} ({plug['ip']})")
                        print(f"     State: {plug['state'].upper()}")
                        print(f"     Current: {plug['current_power']}W")
                        print(f"     Today: {plug['today_energy']}Wh ({plug['today_runtime']}h)")
                        print(f"     Month: {plug['month_energy']}Wh ({plug['month_runtime']}h)")
                    else:
                        print(f"\n  ❌ {plug['name']} ({plug['ip']}) - OFFLINE")
            
            print("\n" + "=" * 70 + "\n")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

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
    subparsers.add_parser("status", help="Show status of all servers and plugs")
    
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
            client.get_status()
    
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted")
        sys.exit(1)


if __name__ == "__main__":
    main()
