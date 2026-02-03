"""CLI entry point for Homelab client"""

import sys
import argparse
from pathlib import Path
from homelab_client.client import HomelabClient


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Homelab Management CLI Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
    status_parser = subparsers.add_parser(
        "status", help="Show status of all servers and plugs"
    )
    status_parser.add_argument(
        "-f",
        "--follow",
        nargs="?",
        const=5.0,
        type=float,
        metavar="INTERVAL",
        help="Continuously update status (default: 5s, e.g., -f 0.5 for 500ms, -f 60 for 1min)",
    )
    status_parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    # Set command (for settings)
    set_parser = subparsers.add_parser("set", help="Set configuration values")
    set_sub = set_parser.add_subparsers(dest="setting", required=True)

    price_parser = set_sub.add_parser("price", help="Set electricity price per kWh")
    price_parser.add_argument("value", type=float, help="Price per kWh (e.g., 0.2721)")

    # Get command (for settings)
    get_parser = subparsers.add_parser("get", help="Get configuration values")
    get_sub = get_parser.add_subparsers(dest="setting", required=True)
    get_sub.add_parser("price", help="Get current electricity price")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Handle config commands specially (don't need full client init)
    if args.command == "config":
        # Create a minimal client instance for config operations
        from homelab_client.config import ConfigManager

        config_mgr = ConfigManager()

        if args.action == "set-server":
            config_mgr.set_server_url(args.url)
            print(f"✓ Server URL set to: {args.url}")
            return
        elif args.action == "set-key":
            config_mgr.set_api_key(args.key)
            print("✓ API key saved")
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
                    print(
                        "Usage: lab server edit <name> [--hostname HOST] [--mac MAC] [--plug PLUG]"
                    )
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
            follow_interval = (
                args.follow if hasattr(args, "follow") and args.follow else None
            )
            use_color = not args.no_color if hasattr(args, "no_color") else True
            client.get_status(follow_interval=follow_interval, use_color=use_color)

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
