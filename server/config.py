"""
Configuration Manager for Homelab Server
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for plugs and servers"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("/app/data/config.json")
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> Dict:
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                return {"plugs": {}, "servers": {}}
        return {"plugs": {}, "servers": {}}

    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.data, f, indent=2)
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    def get_plug(self, name: str) -> Optional[Dict]:
        """Get plug configuration by name"""
        return self.data.get("plugs", {}).get(name)

    def get_server(self, name: str) -> Optional[Dict]:
        """Get server configuration by name"""
        return self.data.get("servers", {}).get(name)

    def list_plugs(self) -> Dict:
        """List all plugs"""
        return self.data.get("plugs", {})

    def list_servers(self) -> Dict:
        """List all servers"""
        return self.data.get("servers", {})

    def add_plug(self, name: str, ip: str):
        """Add or update a plug"""
        if "plugs" not in self.data:
            self.data["plugs"] = {}
        self.data["plugs"][name] = {"ip": ip}
        self.save()

    def remove_plug(self, name: str) -> bool:
        """Remove a plug"""
        if name in self.data.get("plugs", {}):
            del self.data["plugs"][name]
            self.save()
            return True
        return False

    def add_server(self, name: str, hostname: str, mac: Optional[str] = None, plug_name: Optional[str] = None):
        """Add or update a server"""
        if "servers" not in self.data:
            self.data["servers"] = {}
        self.data["servers"][name] = {
            "hostname": hostname,
            "mac": mac or "",
            "plug": plug_name
        }
        self.save()

    def update_server(self, name: str, hostname: Optional[str] = None, mac: Optional[str] = None, plug_name: Optional[str] = None):
        """Update server fields"""
        if name not in self.data.get("servers", {}):
            return False
        
        server = self.data["servers"][name]
        if hostname is not None:
            server["hostname"] = hostname
        if mac is not None:
            server["mac"] = mac
        if plug_name is not None:
            server["plug"] = plug_name
        
        self.save()
        return True

    def update_plug(self, name: str, ip: str):
        """Update plug IP address"""
        if name not in self.data.get("plugs", {}):
            return False
        
        self.data["plugs"][name]["ip"] = ip
        self.save()
        return True

    def remove_server(self, name: str) -> bool:
        """Remove a server"""
        if name in self.data.get("servers", {}):
            del self.data["servers"][name]
            self.save()
            return True
        return False
