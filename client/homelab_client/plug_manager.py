"""Plug management operations"""

from .api_client import APIClient


class PlugManager:
    """Manages smart plug operations"""

    def __init__(self, api_client: APIClient):
        self.api = api_client

    def list_plugs(self):
        """List all plugs"""
        data = self.api._get("/plugs")
        plugs = data["plugs"]

        if not plugs:
            print("No plugs configured")
            return

        print("\nConfigured Plugs:")
        print("-" * 40)
        for idx, (name, plug_data) in enumerate(plugs.items(), 1):
            print(f"{idx}. {name}")
            print(f"   IP: {plug_data['ip']}")
        print()

    def add_plug(self, name: str, ip: str):
        """Add a plug"""
        self.api._post("/plugs", {"name": name, "ip": ip})
        print(f"✓ Plug '{name}' added successfully")

    def edit_plug(self, name: str, ip: str):
        """Edit plug IP address"""
        self.api._put("/plugs", {"name": name, "ip": ip})
        print(f"✓ Plug '{name}' updated successfully")

    def remove_plug(self, name: str):
        """Remove a plug"""
        self.api._delete("/plugs", {"name": name})
        print(f"✓ Plug '{name}' removed successfully")
