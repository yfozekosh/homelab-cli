"""
Configuration Manager for Homelab Server
"""

import os
import json
import logging
import fcntl
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

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
                with open(self.config_path, "r") as f:
                    # Acquire shared lock for reading
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                    try:
                        data = json.load(f)
                        return data
                    finally:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                return {
                    "plugs": {},
                    "servers": {},
                    "state": {},
                    "settings": {"electricity_price": 0.0},
                }
        return {
            "plugs": {},
            "servers": {},
            "state": {},
            "settings": {"electricity_price": 0.0},
        }

    def save(self, backup: bool = True):
        """Save configuration to file atomically with file locking"""
        try:
            # Create backup of existing config
            if backup and self.config_path.exists():
                backup_path = self.config_path.with_suffix('.json.bak')
                try:
                    shutil.copy2(self.config_path, backup_path)
                except Exception as e:
                    logger.warning(f"Failed to create backup: {e}")
            
            # Write to temporary file first
            temp_fd, temp_path = tempfile.mkstemp(
                dir=self.config_path.parent, 
                prefix='.config_', 
                suffix='.tmp'
            )
            
            try:
                with os.fdopen(temp_fd, 'w') as f:
                    # Acquire exclusive lock
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    try:
                        json.dump(self.data, f, indent=2)
                        f.flush()
                        os.fsync(f.fileno())  # Ensure data is written to disk
                    finally:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                
                # Atomic rename
                os.replace(temp_path, self.config_path)
                logger.debug("Configuration saved atomically")
                
            except Exception as e:
                # Clean up temp file on error
                try:
                    os.unlink(temp_path)
                except:
                    pass
                raise e
                
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    def reload(self):
        """Reload configuration from file"""
        self.data = self._load()
        logger.debug("Configuration reloaded")

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

    def add_server(
        self,
        name: str,
        hostname: str,
        mac: Optional[str] = None,
        plug_name: Optional[str] = None,
    ):
        """Add or update a server"""
        if "servers" not in self.data:
            self.data["servers"] = {}
        self.data["servers"][name] = {
            "hostname": hostname,
            "mac": mac or "",
            "plug": plug_name,
        }
        self.save()

    def update_server(
        self,
        name: str,
        hostname: Optional[str] = None,
        mac: Optional[str] = None,
        plug_name: Optional[str] = None,
    ):
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

    def update_server_state(self, name: str, online: bool):
        """Update server online state and track uptime - only saves if state changed"""
        if "state" not in self.data:
            self.data["state"] = {}

        state_changed = False
        
        if name not in self.data["state"]:
            # New server state
            self.data["state"][name] = {
                "online": online,
                "last_change": datetime.utcnow().isoformat(),
                "uptime_start": datetime.utcnow().isoformat() if online else None,
            }
            state_changed = True
        else:
            current_state = self.data["state"][name].get("online", False)
            if current_state != online:
                # State changed
                self.data["state"][name]["online"] = online
                self.data["state"][name]["last_change"] = datetime.utcnow().isoformat()
                if online:
                    self.data["state"][name]["uptime_start"] = datetime.utcnow().isoformat()
                else:
                    self.data["state"][name]["uptime_start"] = None
                state_changed = True

        # Only save if state actually changed to reduce I/O
        if state_changed:
            logger.info(f"Server state changed for {name}: online={online}")
            self.save(backup=False)  # Don't backup on state changes (too frequent)

    def get_server_state(self, name: str) -> Optional[Dict]:
        """Get server state information"""
        return self.data.get("state", {}).get(name)

    def set_electricity_price(self, price: float):
        """Set electricity price per kWh"""
        if "settings" not in self.data:
            self.data["settings"] = {}
        self.data["settings"]["electricity_price"] = price
        self.save()

    def get_electricity_price(self) -> float:
        """Get electricity price per kWh"""
        return self.data.get("settings", {}).get("electricity_price", 0.0)

    def remove_server(self, name: str) -> bool:
        """Remove a server"""
        if name in self.data.get("servers", {}):
            del self.data["servers"][name]
            self.save()
            return True
        return False
