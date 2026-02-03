"""Server management operations"""

from typing import Optional
from .api_client import APIClient


class ServerManager:
    """Manages homelab server operations"""

    def __init__(self, api_client: APIClient):
        self.api = api_client

    def list_servers(self):
        """List all servers"""
        data = self.api._get("/servers")
        servers = data["servers"]

        if not servers:
            print("No servers configured")
            return

        print("\nConfigured Servers:")
        print("-" * 60)
        for idx, (name, server_data) in enumerate(servers.items(), 1):
            status = "🟢 Online" if server_data.get("online") else "🔴 Offline"
            print(f"{idx}. {name} - {status}")
            print(f"   Hostname: {server_data['hostname']}")
            print(f"   MAC: {server_data['mac']}")
            print(f"   Plug: {server_data.get('plug', 'None')}")
            print(f"   IP: {server_data.get('ip', 'Unknown')}")
            print()

    def add_server(
        self,
        name: str,
        hostname: str,
        mac: Optional[str] = None,
        plug: Optional[str] = None,
    ):
        """Add a server"""
        self.api._post(
            "/servers", {"name": name, "hostname": hostname, "mac": mac, "plug": plug}
        )
        print(f"✓ Server '{name}' added successfully")

    def edit_server(
        self,
        name: str,
        hostname: Optional[str] = None,
        mac: Optional[str] = None,
        plug: Optional[str] = None,
    ):
        """Edit server configuration"""
        data = {"name": name}
        if hostname is not None:
            data["hostname"] = hostname
        if mac is not None:
            data["mac"] = mac
        if plug is not None:
            data["plug"] = plug

        self.api._put("/servers", data)
        print(f"✓ Server '{name}' updated successfully")

    def remove_server(self, name: str):
        """Remove a server"""
        self.api._delete("/servers", {"name": name})
        print(f"✓ Server '{name}' removed successfully")
