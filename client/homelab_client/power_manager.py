"""Power control operations"""

import sys
from .api_client import APIClient


class PowerManager:
    """Manages server power operations"""

    def __init__(self, api_client: APIClient):
        self.api = api_client

    def power_on(self, name: str):
        """Power on a server"""
        print(f"⚡ Powering on server '{name}'...")
        result = self.api._post("/power/on", {"name": name}, timeout=180)

        if result.get("success"):
            print(f"✓ Server '{name}' powered on successfully")
            if result.get("logs"):
                print("\nLogs:")
                for log in result["logs"][-5:]:  # Show last 5 logs
                    print(f"  {log}")
        else:
            print(f"❌ Failed: {result.get('message')}")
            sys.exit(1)

    def power_off(self, name: str):
        """Power off a server"""
        print(f"🔴 Powering off server '{name}'...")
        result = self.api._post("/power/off", {"name": name}, timeout=180)

        if result.get("success"):
            print(f"✓ Server '{name}' powered off successfully")
            if result.get("logs"):
                print("\nLogs:")
                for log in result["logs"][-5:]:
                    print(f"  {log}")
        else:
            print(f"⚠️  {result.get('message')}")
