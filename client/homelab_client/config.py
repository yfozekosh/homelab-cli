"""Configuration management for Homelab client"""

import json
from pathlib import Path
from typing import Optional


class ConfigManager:
    """Manages client configuration storage and retrieval"""

    def __init__(self):
        self.config_dir = Path.home() / ".config" / "homelab-client"
        self.config_file = self.config_dir / "config.json"

    def load_config(self) -> dict:
        """Load client configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_config(self, config: dict):
        """Save client configuration to file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)

    def get_server_url(
        self, env_var: Optional[str] = None, param: Optional[str] = None
    ) -> Optional[str]:
        """Get server URL from parameter, config file, or environment"""
        if param:
            return param
        config = self.load_config()
        return config.get("server_url") or env_var

    def get_api_key(
        self, env_var: Optional[str] = None, param: Optional[str] = None
    ) -> Optional[str]:
        """Get API key from parameter, config file, or environment"""
        if param:
            return param
        config = self.load_config()
        return config.get("api_key") or env_var

    def set_server_url(self, url: str):
        """Save server URL to config"""
        config = self.load_config()
        config["server_url"] = url
        self.save_config(config)

    def set_api_key(self, key: str):
        """Save API key to config"""
        config = self.load_config()
        config["api_key"] = key
        self.save_config(config)
