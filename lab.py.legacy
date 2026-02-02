#!/usr/bin/env python3
"""
Lab - Smart Plug and Server Management CLI
Manages Tapo smart plugs and servers with power monitoring
"""

import sys
import json
import logging
import argparse
import asyncio
import time
import subprocess
from pathlib import Path
from typing import Optional, Dict
from tapo import ApiClient
from wakeonlan import send_magic_packet

# Configuration
CONFIG_DIR = Path.home() / ".config" / "lab"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE = CONFIG_DIR / "lab.log"

# Setup logging
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("lab")


class Config:
    """Configuration manager for plugs and servers"""

    def __init__(self):
        self.data = self._load()

    def _load(self) -> Dict:
        """Load configuration from file"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                return {"plugs": {}, "servers": {}}
        return {"plugs": {}, "servers": {}}

    def _save(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.data, f, indent=2)
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise


class PlugManager:
    """Manages Tapo smart plugs"""

    def __init__(self, config: Config):
        self.config = config

    def add(self, name: str, ip: str):
        """Add a new plug"""
        if name in self.config.data["plugs"]:
            logger.warning(f"Plug '{name}' already exists, updating...")

        self.config.data["plugs"][name] = {"ip": ip}
        self.config._save()
        logger.info(f"Added plug '{name}' at {ip}")
        print(f"✓ Plug '{name}' added successfully")

    def remove(self, name: str):
        """Remove a plug"""
        if name not in self.config.data["plugs"]:
            logger.error(f"Plug '{name}' not found")
            print(f"✗ Plug '{name}' not found")
            return

        del self.config.data["plugs"][name]
        self.config._save()
        logger.info(f"Removed plug '{name}'")
        print(f"✓ Plug '{name}' removed successfully")

    def list(self):
        """List all plugs"""
        plugs = self.config.data["plugs"]
        if not plugs:
            print("No plugs configured")
            return

        print("\nConfigured Plugs:")
        print("-" * 40)
        for idx, (name, data) in enumerate(plugs.items(), 1):
            print(f"{idx}. {name}")
            print(f"   IP: {data['ip']}")
        print()

    async def get_client(self, name: str):
        """Get Tapo client for a plug"""
        if name not in self.config.data["plugs"]:
            raise ValueError(f"Plug '{name}' not found")

        ip = self.config.data["plugs"][name]["ip"]
        # Note: You'll need to set TAPO_USERNAME and TAPO_PASSWORD env vars
        # or modify this to accept credentials
        import os
        username = os.getenv("TAPO_USERNAME")
        password = os.getenv("TAPO_PASSWORD")

        if not username or not password:
            raise ValueError(
                "TAPO_USERNAME and TAPO_PASSWORD environment variables must be set")

        client = ApiClient(username, password)
        device = await client.p110(ip)
        return device

    async def turn_on(self, name: str):
        """Turn on a plug"""
        logger.info(f"Turning on plug '{name}'")
        device = await self.get_client(name)
        await device.on()
        logger.info(f"Plug '{name}' turned on")

    async def turn_off(self, name: str):
        """Turn off a plug"""
        logger.info(f"Turning off plug '{name}'")
        device = await self.get_client(name)
        await device.off()
        logger.info(f"Plug '{name}' turned off")

    async def get_power(self, name: str) -> float:
        """Get current power usage in watts"""
        device = await self.get_client(name)
        energy = await device.get_current_power()
        return energy.current_power


class ServerManager:
    """Manages servers"""

    def __init__(self, config: Config):
        self.config = config

    def add(self, name: str, hostname: str, mac: str, plug_name: Optional[str] = None):
        """Add a new server"""
        if name in self.config.data["servers"]:
            logger.warning(f"Server '{name}' already exists, updating...")

        self.config.data["servers"][name] = {
            "hostname": hostname,
            "mac": mac,
            "plug": plug_name
        }
        self.config._save()
        logger.info(f"Added server '{name}'")
        print(f"✓ Server '{name}' added successfully")

    def remove(self, name: str):
        """Remove a server"""
        if name not in self.config.data["servers"]:
            logger.error(f"Server '{name}' not found")
            print(f"✗ Server '{name}' not found")
            return

        del self.config.data["servers"][name]
        self.config._save()
        logger.info(f"Removed server '{name}'")
        print(f"✓ Server '{name}' removed successfully")

    def list(self):
        """List all servers"""
        servers = self.config.data["servers"]
        if not servers:
            print("No servers configured")
            return

        print("\nConfigured Servers:")
        print("-" * 60)
        for idx, (name, data) in enumerate(servers.items(), 1):
            print(f"{idx}. {name}")
            print(f"   Hostname: {data['hostname']}")
            print(f"   MAC: {data['mac']}")
            print(f"   Plug: {data.get('plug', 'None')}")

            # Run nslookup
            try:
                result = subprocess.run(
                    ["nslookup", data['hostname']],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Extract IP from nslookup output
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Address:' in line and '#53' not in line:
                            ip = line.split('Address:')[1].strip()
                            print(f"   Resolved IP: {ip}")
                            break
                else:
                    print(f"   Resolved IP: Unable to resolve")
            except Exception as e:
                logger.warning(f"nslookup failed for {data['hostname']}: {e}")
                print(f"   Resolved IP: Error resolving")
            print()

    def ping(self, hostname: str, timeout: int = 1) -> bool:
        """Ping a server"""
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", str(timeout), hostname],
                capture_output=True,
                timeout=timeout + 1
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Ping failed: {e}")
            return False

    def send_wol(self, mac: str):
        """Send Wake-on-LAN packet"""
        logger.info(f"Sending WOL packet to {mac}")
        send_magic_packet(mac)

    def shutdown(self, hostname: str):
        """Send shutdown command to server"""
        logger.info(f"Sending shutdown command to {hostname}")
        try:
            subprocess.run(
                ["ssh", "-t", f"{hostname}", "sudo", "poweroff"],
                timeout=60
            )
        except Exception as e:
            logger.error(f"Failed to send shutdown: {e}")
            raise


class PowerController:
    """Controls server power with plug monitoring"""

    def __init__(self, config: Config):
        self.config = config
        self.plug_mgr = PlugManager(config)
        self.server_mgr = ServerManager(config)

    async def power_on(self, name: str):
        """Power on a server"""
        if name not in self.config.data["servers"]:
            print(f"✗ Server '{name}' not found")
            return

        server = self.config.data["servers"][name]
        plug_name = server.get("plug")

        if not plug_name:
            print(f"✗ No plug associated with server '{name}'")
            return

        print(f"Powering on server '{name}'...")

        # Turn on plug
        await self.plug_mgr.turn_on(plug_name)
        print("✓ Plug turned on")

        # Monitor for 30 seconds
        print("Monitoring server boot (60s)...")
        success = await self._monitor_boot(server, plug_name, 60)

        if not success:
            power = await self.plug_mgr.get_power(plug_name)
            print(f"⚠ Server not responding (power: {power:.1f}W)")

            if power < 5.0:
                print("Sending Wake-on-LAN packet...")
                self.server_mgr.send_wo6(server["mac"])

                # Monitor for another 30 seconds
                print("Monitoring server boot (60s)...")
                success = await self._monitor_boot(server, plug_name, 60)

                if not success:
                    print("✗ Server failed to boot")
                    print("Turning off plug...")
                    await self.plug_mgr.turn_off(plug_name)
                    return

        print(f"✓ Server '{name}' is online")

    async def _monitor_boot(
            self,
            server: Dict,
            plug_name: str,
            duration: int) -> bool:
        """Monitor server boot process"""
        start = time.time()
        last_ping = False

        while time.time() - start < duration:
            passed = int(time.time() - start)
            # Check ping
            if self.server_mgr.ping(server["hostname"]):
                if not last_ping:
                    print("✓ Server responding to ping")
                return True

            # Check power
            try:
                power = await self.plug_mgr.get_power(plug_name)
                print(f" {passed:02}  Power: {power:.1f}W       ", end='\r')
            except Exception as e:
                logger.warning(f"Failed to read power: {e}")

            await asyncio.sleep(1)
            last_ping = False

        return False

    async def power_off(self, name: str):
        """Power off a server"""
        if name not in self.config.data["servers"]:
            print(f"✗ Server '{name}' not found")
            return

        server = self.config.data["servers"][name]
        plug_name = server.get("plug")

        if not plug_name:
            print(f"✗ No plug associated with server '{name}'")
            return

        print(f"Powering off server '{name}'...")

        # Send shutdown command
        try:
            self.server_mgr.shutdown(server["hostname"])
            print("✓ Shutdown command sent")
        except Exception as e:
            print(f"⚠ Failed to send shutdown: {e}")
            print("Continuing with power monitoring...")

        # Monitor shutdown
        print("Monitoring server shutdown...")
        start = time.time()
        timeout = 120  # 2 minutes max
        timestampOfLowPower = None

        while time.time() - start < timeout:
            passed = int(time.time() - start)
            # Check power
            try:
                power = await self.plug_mgr.get_power(plug_name)
                print(f" {passed:02}  Power: {power:.1f}W", end='\r')

                if power < 5.0:
                    if timestampOfLowPower is None:
                        timestampOfLowPower = time.time()
                    if time.time() - timestampOfLowPower > 10:
                        print(f"\n✓ Server powered down (power: {power:.1f}W)")
                        break
            except Exception as e:
                logger.warning(f"Failed to read power: {e}")

            await asyncio.sleep(2)
        else:
            print("\n⚠ Timeout waiting for shutdown")

        # Turn off plug
        print("Turning off plug...")
        await self.plug_mgr.turn_off(plug_name)
        print(f"✓ Server '{name}' is offline")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Lab - Smart Plug and Server Management")
    subparsers = parser.add_subparsers(
        dest="command", help="Command to execute")

    # Plug commands
    plug_parser = subparsers.add_parser("plug", help="Manage plugs")
    plug_sub = plug_parser.add_subparsers(dest="action")

    plug_add = plug_sub.add_parser("add", help="Add a plug")
    plug_add.add_argument("name", help="Plug name")
    plug_add.add_argument("ip", help="Plug IP address")

    plug_remove = plug_sub.add_parser("remove", help="Remove a plug")
    plug_remove.add_argument("name", help="Plug name")

    plug_sub.add_parser("list", help="List plugs")

    # Server commands
    server_parser = subparsers.add_parser("server", help="Manage servers")
    server_sub = server_parser.add_subparsers(dest="action")

    server_add = server_sub.add_parser("add", help="Add a server")
    server_add.add_argument("name", help="Server name")
    server_add.add_argument("hostname", help="Server hostname")
    server_add.add_argument("mac", help="Server MAC address")
    server_add.add_argument("plug", nargs="?", help="Associated plug name")

    server_remove = server_sub.add_parser("remove", help="Remove a server")
    server_remove.add_argument("name", help="Server name")

    server_sub.add_parser("list", help="List servers")

    # Power commands
    on_parser = subparsers.add_parser("on", help="Power on a server")
    on_parser.add_argument("name", help="Server name")

    off_parser = subparsers.add_parser("off", help="Power off a server")
    off_parser.add_argument("name", help="Server name")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    config = Config()

    try:
        if args.command == "plug":
            plug_mgr = PlugManager(config)
            if args.action == "add":
                plug_mgr.add(args.name, args.ip)
            elif args.action == "remove":
                plug_mgr.remove(args.name)
            elif args.action == "list":
                plug_mgr.list()

        elif args.command == "server":
            server_mgr = ServerManager(config)
            if args.action == "add":
                server_mgr.add(args.name, args.hostname, args.mac, args.plug)
            elif args.action == "remove":
                server_mgr.remove(args.name)
            elif args.action == "list":
                server_mgr.list()

        elif args.command == "on":
            controller = PowerController(config)
            asyncio.run(controller.power_on(args.name))

        elif args.command == "off":
            controller = PowerController(config)
            asyncio.run(controller.power_off(args.name))

    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
