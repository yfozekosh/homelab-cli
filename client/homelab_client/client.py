"""Main Homelab client class - facade for all operations"""

import sys
import os
from typing import Optional
from .config import ConfigManager
from .api_client import APIClient
from .plug_manager import PlugManager
from .server_manager import ServerManager
from .power_manager import PowerManager
from .price_manager import PriceManager
from .status_manager import StatusManager


class HomelabClient:
    """Main client facade for Homelab API operations"""

    def __init__(self, server_url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize the Homelab client

        Args:
            server_url: Server URL (overrides config/env)
            api_key: API key (overrides config/env)
        """
        self.config_manager = ConfigManager()

        # Resolve configuration from parameters, config file, or environment
        env_url = os.getenv("HOMELAB_SERVER_URL")
        env_key = os.getenv("HOMELAB_API_KEY")

        self.server_url = self.config_manager.get_server_url(env_url, server_url)
        self.api_key = self.config_manager.get_api_key(env_key, api_key)

        # Validate required configuration
        if not self.server_url:
            print("❌ Error: Server URL not configured.")
            print(
                "Set HOMELAB_SERVER_URL environment variable or run: lab config set-server <url>"
            )
            sys.exit(1)

        if not self.api_key:
            print("❌ Error: API key not configured.")
            print(
                "Set HOMELAB_API_KEY environment variable or run: lab config set-key <key>"
            )
            sys.exit(1)

        # Initialize API client and managers
        self.api = APIClient(self.server_url, self.api_key)
        self.plugs = PlugManager(self.api)
        self.servers = ServerManager(self.api)
        self.power = PowerManager(self.api)
        self.price = PriceManager(self.api)
        self.status = StatusManager(self.api)

    # Expose configuration path for tests
    @property
    def config_dir(self):
        return self.config_manager.config_dir

    @property
    def config_file(self):
        return self.config_manager.config_file

    @property
    def headers(self):
        """Expose headers for tests compatibility"""
        return self.api.headers

    # Configuration methods
    def _load_config(self) -> dict:
        """Load client configuration"""
        return self.config_manager.load_config()

    def _save_config(self, config: dict):
        """Save client configuration"""
        self.config_manager.save_config(config)

    def set_server_url(self, url: str):
        """Set server URL in config"""
        self.config_manager.set_server_url(url)
        print(f"✓ Server URL set to: {url}")

    def set_api_key(self, key: str):
        """Set API key in config"""
        self.config_manager.set_api_key(key)
        print("✓ API key saved")

    # Health check
    def health_check(self) -> bool:
        """Check server health"""
        return self.api.health_check()

    # Plug operations - delegate to PlugManager
    def list_plugs(self):
        """List all plugs"""
        self.plugs.list_plugs()

    def add_plug(self, name: str, ip: str):
        """Add a plug"""
        self.plugs.add_plug(name, ip)

    def edit_plug(self, name: str, ip: str):
        """Edit plug IP address"""
        self.plugs.edit_plug(name, ip)

    def remove_plug(self, name: str):
        """Remove a plug"""
        self.plugs.remove_plug(name)

    # Server operations - delegate to ServerManager
    def list_servers(self):
        """List all servers"""
        self.servers.list_servers()

    def add_server(
        self,
        name: str,
        hostname: str,
        mac: Optional[str] = None,
        plug: Optional[str] = None,
    ):
        """Add a server"""
        self.servers.add_server(name, hostname, mac, plug)

    def edit_server(
        self,
        name: str,
        hostname: Optional[str] = None,
        mac: Optional[str] = None,
        plug: Optional[str] = None,
    ):
        """Edit server configuration"""
        self.servers.edit_server(name, hostname, mac, plug)

    def remove_server(self, name: str):
        """Remove a server"""
        self.servers.remove_server(name)

    # Power operations - delegate to PowerManager
    def power_on(self, name: str):
        """Power on a server"""
        self.power.power_on(name)

    def power_off(self, name: str):
        """Power off a server"""
        self.power.power_off(name)

    # Price operations - delegate to PriceManager
    def set_electricity_price(self, price: float):
        """Set electricity price per kWh"""
        self.price.set_electricity_price(price)

    def get_electricity_price(self):
        """Get current electricity price"""
        self.price.get_electricity_price()

    # Status operations - delegate to StatusManager
    def get_status(
        self, follow_interval: Optional[float] = None, use_color: bool = True
    ):
        """Get comprehensive status of all servers and plugs"""
        self.status.get_status(follow_interval, use_color)

    # Internal method for tests compatibility
    def _wait_for_input(self, interval: float, stop_event):
        """Wait for input - delegates to StatusManager"""
        return self.status._wait_for_input(interval, stop_event)
