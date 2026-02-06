"""
Telegram Bot for Homelab Management
"""

import os
import logging
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import Config
from .plug_service import PlugService
from .server_service import ServerService
from .power_service import PowerControlService
from .status_service import StatusService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HomelabBot:
    """Telegram bot for homelab management"""

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable must be set")

        # Parse allowed user IDs
        user_ids_str = os.getenv("TELEGRAM_USER_IDS", "")
        self.allowed_users: List[int] = []
        if user_ids_str:
            try:
                self.allowed_users = [
                    int(uid.strip()) for uid in user_ids_str.split(",")
                ]
            except ValueError:
                logger.error(
                    "Invalid TELEGRAM_USER_IDS format. Expected comma-separated integers."
                )
                raise

        logger.info(f"Allowed user IDs: {self.allowed_users}")

        # Initialize services
        config_path = Path(os.getenv("CONFIG_PATH", "/app/data/config.json"))
        self.config = Config(config_path)
        self.plug_service = PlugService()
        self.server_service = ServerService()
        self.power_service = PowerControlService(self.plug_service, self.server_service)
        self.status_service = StatusService(
            self.config, self.plug_service, self.server_service
        )

        # Build application
        self.app = Application.builder().token(self.token).build()
        self._setup_handlers()

    def _check_access(self, user_id: int) -> bool:
        """Check if user has access"""
        if not self.allowed_users:
            logger.warning("No user IDs configured. Allowing all users.")
            return True
        return user_id in self.allowed_users

    def _setup_handlers(self):
        """Setup command and callback handlers"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("menu", self.menu_command))
        self.app.add_handler(CommandHandler("servers", self.servers_command))
        self.app.add_handler(CommandHandler("plugs", self.plugs_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("on", self.on_command))
        self.app.add_handler(CommandHandler("off", self.off_command))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.unknown_message)
        )

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id

        if not self._check_access(user_id):
            await update.message.reply_text(
                "❌ Access denied. Your user ID is not authorized.\n"
                f"Your ID: {user_id}"
            )
            return

        await update.message.reply_text(
            "🏠 *Homelab Management Bot*\n\n"
            "Welcome! Use buttons or commands:\n\n"
            "*Commands:*\n"
            "`/status` - Full status overview\n"
            "`/status <server>` - Server details\n"
            "`/on <server>` - Power on server\n"
            "`/off <server>` - Power off server\n"
            "`/servers` - List servers\n"
            "`/plugs` - List plugs\n"
            "`/menu` - Show menu",
            parse_mode="Markdown",
            reply_markup=self._get_main_menu(),
        )

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command"""
        user_id = update.effective_user.id

        if not self._check_access(user_id):
            await update.message.reply_text("❌ Access denied.")
            return

        await update.message.reply_text(
            "🏠 Main Menu:", reply_markup=self._get_main_menu()
        )

    async def servers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /servers command"""
        user_id = update.effective_user.id

        if not self._check_access(user_id):
            await update.message.reply_text("❌ Access denied.")
            return

        servers = self.config.list_servers()

        if not servers:
            await update.message.reply_text("No servers configured.")
            return

        keyboard = []
        for name, server in servers.items():
            online = self.server_service.ping(server["hostname"])
            status = "🟢" if online else "🔴"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{status} {name}", callback_data=f"server:{name}"
                    )
                ]
            )

        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu")])

        await update.message.reply_text(
            "🖥️ *Servers:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    async def plugs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /plugs command"""
        user_id = update.effective_user.id

        if not self._check_access(user_id):
            await update.message.reply_text("❌ Access denied.")
            return

        plugs = self.config.list_plugs()

        if not plugs:
            await update.message.reply_text("No plugs configured.")
            return

        text = "🔌 *Plugs:*\n\n"
        for name, plug in plugs.items():
            text += f"• {name} ({plug['ip']})\n"

        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="menu")]]

        await update.message.reply_text(
            text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status [server_name] command"""
        user_id = update.effective_user.id

        if not self._check_access(user_id):
            await update.message.reply_text("❌ Access denied.")
            return

        args = context.args
        if args:
            # Show specific server status
            server_name = args[0]
            await self._send_server_status(update.message, server_name)
        else:
            # Show full status
            await self._send_full_status(update.message)

    async def on_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /on <server_name> command"""
        user_id = update.effective_user.id

        if not self._check_access(user_id):
            await update.message.reply_text("❌ Access denied.")
            return

        args = context.args
        if not args:
            await update.message.reply_text(
                "Usage: `/on <server_name>`\n\n"
                "Example: `/on main-srv`",
                parse_mode="Markdown",
            )
            return

        server_name = args[0]
        await self._power_on_server_msg(update.message, server_name)

    async def off_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /off <server_name> command"""
        user_id = update.effective_user.id

        if not self._check_access(user_id):
            await update.message.reply_text("❌ Access denied.")
            return

        args = context.args
        if not args:
            await update.message.reply_text(
                "Usage: `/off <server_name>`\n\n"
                "Example: `/off main-srv`",
                parse_mode="Markdown",
            )
            return

        server_name = args[0]
        await self._power_off_server_msg(update.message, server_name)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        user_id = query.from_user.id

        if not self._check_access(user_id):
            await query.answer("❌ Access denied.", show_alert=True)
            return

        await query.answer()

        data = query.data

        if data == "menu":
            await query.edit_message_text(
                "🏠 Main Menu:", reply_markup=self._get_main_menu()
            )

        elif data == "servers":
            await self._show_servers_list(query)

        elif data == "plugs":
            await self._show_plugs_list(query)

        elif data.startswith("server:"):
            server_name = data.split(":", 1)[1]
            await self._show_server_details(query, server_name)

        elif data.startswith("power_on:"):
            server_name = data.split(":", 1)[1]
            await self._power_on_server(query, server_name)

        elif data.startswith("power_off:"):
            server_name = data.split(":", 1)[1]
            await self._power_off_server(query, server_name)

        elif data.startswith("confirm_off:"):
            server_name = data.split(":", 1)[1]
            await self._confirm_power_off(query, server_name)

        elif data.startswith("cancel:"):
            await query.edit_message_text(
                "❌ Action cancelled.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")]]
                ),
            )

        elif data == "noop":
            # No operation - just acknowledge
            await query.answer("Configuration required via CLI", show_alert=True)

        elif data == "status_refresh":
            await self._refresh_status(query)

    async def unknown_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown messages"""
        await update.message.reply_text(
            "Use /menu to see available commands.", reply_markup=self._get_main_menu()
        )

    def _get_main_menu(self) -> InlineKeyboardMarkup:
        """Get main menu keyboard"""
        keyboard = [
            [InlineKeyboardButton("📊 Status", callback_data="status_refresh")],
            [InlineKeyboardButton("🖥️ Servers", callback_data="servers")],
            [InlineKeyboardButton("🔌 Plugs", callback_data="plugs")],
        ]
        return InlineKeyboardMarkup(keyboard)

    async def _refresh_status(self, query):
        """Refresh and show full status"""
        try:
            status = await self.status_service.get_all_status()
            text = self._format_status_text(status)

            keyboard = [
                [InlineKeyboardButton("🔄 Refresh", callback_data="status_refresh")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data="menu")],
            ]

            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as e:
            logger.error(f"Failed to refresh status: {e}")
            await query.edit_message_text(
                f"❌ Error getting status: {str(e)}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Back", callback_data="menu")]]
                ),
            )

    async def _show_servers_list(self, query):
        """Show servers list with buttons"""
        servers = self.config.list_servers()

        if not servers:
            await query.edit_message_text(
                "No servers configured.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Back", callback_data="menu")]]
                ),
            )
            return

        keyboard = []
        for name, server in servers.items():
            online = self.server_service.ping(server["hostname"])
            status = "🟢" if online else "🔴"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{status} {name}", callback_data=f"server:{name}"
                    )
                ]
            )

        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu")])

        await query.edit_message_text(
            "🖥️ *Servers:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    async def _show_plugs_list(self, query):
        """Show plugs list"""
        plugs = self.config.list_plugs()

        if not plugs:
            await query.edit_message_text(
                "No plugs configured.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Back", callback_data="menu")]]
                ),
            )
            return

        text = "🔌 *Plugs:*\n\n"
        for name, plug in plugs.items():
            text += f"• {name} ({plug['ip']})\n"

        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="menu")]]

        await query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def _show_server_details(self, query, server_name: str):
        """Show server details with action buttons (detailed like CLI)"""
        server_data = self.config.get_server(server_name)

        if not server_data:
            await query.edit_message_text(
                f"❌ Server '{server_name}' not found.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Back", callback_data="servers")]]
                ),
            )
            return

        try:
            server_status = await self.status_service.get_server_status(server_name, server_data)
            text = self._format_server_status_text(server_status)

            keyboard = []

            if server_data.get("plug"):
                if server_data.get("mac"):
                    if not server_status["online"]:
                        keyboard.append([
                            InlineKeyboardButton("⚡ Power On", callback_data=f"power_on:{server_name}")
                        ])
                    else:
                        keyboard.append([
                            InlineKeyboardButton("🔴 Power Off", callback_data=f"confirm_off:{server_name}")
                        ])
                else:
                    keyboard.append([
                        InlineKeyboardButton("⚠️ Cannot power on (no MAC)", callback_data="noop")
                    ])

            keyboard.append([
                InlineKeyboardButton("🔄 Refresh", callback_data=f"server:{server_name}"),
                InlineKeyboardButton("⬅️ Back", callback_data="servers"),
            ])

            await query.edit_message_text(
                text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Failed to get server details: {e}")
            # Fallback to basic info
            online = self.server_service.ping(server_data["hostname"])
            status = "🟢 Online" if online else "🔴 Offline"
            ip = self.server_service.resolve_hostname(server_data["hostname"])

            text = (
                f"🖥️ *{server_name}*\n\n"
                f"Status: {status}\n"
                f"Hostname: `{server_data['hostname']}`\n"
                f"IP: `{ip}`"
            )

            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="servers")]]
            await query.edit_message_text(
                text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
            )

    async def _confirm_power_off(self, query, server_name: str):
        """Show power off confirmation"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Yes, Power Off", callback_data=f"power_off:{server_name}"
                )
            ],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"server:{server_name}")],
        ]

        await query.edit_message_text(
            f"⚠️ Are you sure you want to power off *{server_name}*?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    async def _power_on_server(self, query, server_name: str):
        """Power on a server (via button)"""
        server = self.config.get_server(server_name)

        if not server or not server.get("plug"):
            await query.edit_message_text(
                f"❌ Cannot power on '{server_name}'.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Back", callback_data="servers")]]
                ),
            )
            return

        if not server.get("mac"):
            await query.edit_message_text(
                f"❌ Cannot power on '{server_name}' - no MAC address configured.\n\n"
                f"Use CLI to add MAC address:\n"
                f"`lab server edit {server_name} --mac AA:BB:CC:DD:EE:FF`",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Back", callback_data="servers")]]
                ),
            )
            return

        plug = self.config.get_plug(server["plug"])
        if not plug:
            await query.edit_message_text(
                f"❌ Plug '{server['plug']}' not found.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Back", callback_data="servers")]]
                ),
            )
            return

        await query.edit_message_text(
            f"⚡ *Powering on {server_name}...*\n\n"
            f"Starting...",
            parse_mode="Markdown"
        )

        # Track progress with logs
        logs = []
        last_update = [time.time()]

        async def progress_callback(msg: str):
            logs.append(msg)
            now = time.time()
            if now - last_update[0] >= 2:  # Update every 2 seconds
                try:
                    progress_text = "\n".join(logs[-8:])
                    await query.edit_message_text(
                        f"⚡ *Powering on {server_name}...*\n\n"
                        f"```\n{progress_text}\n```",
                        parse_mode="Markdown",
                    )
                    last_update[0] = now
                except Exception:
                    pass

        try:
            result = await self.power_service.power_on(
                server, plug["ip"], progress_callback
            )

            if result["success"]:
                await query.edit_message_text(
                    f"✅ *{server_name}* powered on successfully!",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 View Status", callback_data=f"server:{server_name}")],
                        [InlineKeyboardButton("⬅️ Back to Servers", callback_data="servers")],
                    ]),
                )
            else:
                progress_text = "\n".join(logs[-5:]) if logs else "No logs"
                await query.edit_message_text(
                    f"❌ Failed to power on *{server_name}*\n\n"
                    f"{result.get('message', 'Unknown error')}\n\n"
                    f"```\n{progress_text}\n```",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Back to Servers", callback_data="servers")]
                    ]),
                )
        except Exception as e:
            logger.error(f"Failed to power on server: {e}")
            await query.edit_message_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Back to Servers", callback_data="servers")]
                ]),
            )

    async def _power_off_server(self, query, server_name: str):
        """Power off a server (via button)"""
        server = self.config.get_server(server_name)

        if not server or not server.get("plug"):
            await query.edit_message_text(
                f"❌ Cannot power off '{server_name}'.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Back", callback_data="servers")]]
                ),
            )
            return

        plug = self.config.get_plug(server["plug"])
        if not plug:
            await query.edit_message_text(
                f"❌ Plug '{server['plug']}' not found.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Back", callback_data="servers")]]
                ),
            )
            return

        await query.edit_message_text(
            f"🔴 *Powering off {server_name}...*\n\n"
            f"Initiating graceful shutdown...",
            parse_mode="Markdown"
        )

        # Track progress with logs
        logs = []
        last_update = [time.time()]

        async def progress_callback(msg: str):
            logs.append(msg)
            now = time.time()
            if now - last_update[0] >= 2:  # Update every 2 seconds
                try:
                    progress_text = "\n".join(logs[-8:])
                    await query.edit_message_text(
                        f"🔴 *Powering off {server_name}...*\n\n"
                        f"```\n{progress_text}\n```",
                        parse_mode="Markdown",
                    )
                    last_update[0] = now
                except Exception:
                    pass

        try:
            result = await self.power_service.power_off(
                server, plug["ip"], progress_callback
            )

            if result["success"]:
                await query.edit_message_text(
                    f"✅ *{server_name}* powered off successfully!",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 View Status", callback_data=f"server:{server_name}")],
                        [InlineKeyboardButton("⬅️ Back to Servers", callback_data="servers")],
                    ]),
                )
            else:
                progress_text = "\n".join(logs[-5:]) if logs else "No logs"
                await query.edit_message_text(
                    f"⚠️ *{server_name}* powered off (with warnings)\n\n"
                    f"{result.get('message', '')}\n\n"
                    f"```\n{progress_text}\n```",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Back to Servers", callback_data="servers")]
                    ]),
                )
        except Exception as e:
            logger.error(f"Failed to power off server: {e}")
            await query.edit_message_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Back to Servers", callback_data="servers")]
                ]),
            )

    def _format_status_text(self, status: Dict) -> str:
        """Format full status as Telegram message (CLI-like)"""
        summary = status["summary"]
        lines = []

        lines.append("📊 *HOMELAB STATUS*")
        lines.append("")

        # Summary section
        lines.append("*Summary:*")
        lines.append(f"  Servers: {summary['servers_online']}/{summary['servers_total']} online")
        lines.append(f"  Plugs: {summary['plugs_on']}/{summary['plugs_total']} on ({summary['plugs_online']} reachable)")
        lines.append(f"  Power: {summary['total_power']:.1f}W total")

        # Servers section
        if status["servers"]:
            lines.append("")
            lines.append("*🖥️ Servers:*")
            for server in status["servers"]:
                status_icon = "🟢" if server["online"] else "🔴"
                lines.append(f"\n{status_icon} *{server['name']}*")
                lines.append(f"  Host: `{server['hostname']}` ({server['ip']})")

                if server["online"] and server.get("uptime"):
                    lines.append(f"  Uptime: {server['uptime']}")
                elif not server["online"] and server.get("downtime"):
                    lines.append(f"  Downtime: {server['downtime']}")

                if server.get("power"):
                    power = server["power"]
                    power_line = f"  ⚡ {power['current']}W"
                    if power.get("current_cost_per_hour", 0) > 0:
                        power_line += f" ({power['current_cost_per_hour']:.4f}€/h)"
                    lines.append(power_line)

                    lines.append(f"  Today: {power['today_energy']}Wh" +
                                (f" ({power['today_cost']:.2f}€)" if power.get('today_cost', 0) > 0 else ""))
                    lines.append(f"  Month: {power['month_energy']}Wh" +
                                (f" ({power['month_cost']:.2f}€)" if power.get('month_cost', 0) > 0 else ""))

        # Plugs section (standalone plugs not attached to servers)
        standalone_plugs = [p for p in status.get("plugs", [])
                          if not any(s.get("plug") == p["name"] for s in status.get("servers", []))]
        if standalone_plugs:
            lines.append("")
            lines.append("*🔌 Plugs:*")
            for plug in standalone_plugs:
                if not plug.get("online"):
                    lines.append(f"\n❌ *{plug['name']}* - OFFLINE")
                    continue

                state_icon = "⚡" if plug["state"] == "on" else "⭕"
                lines.append(f"\n{state_icon} *{plug['name']}* ({plug['state'].upper()})")
                lines.append(f"  IP: `{plug['ip']}`")

                power_line = f"  Power: {plug['current_power']}W"
                if plug.get("current_cost_per_hour", 0) > 0:
                    power_line += f" ({plug['current_cost_per_hour']:.4f}€/h)"
                lines.append(power_line)

                lines.append(f"  Today: {plug['today_energy']}Wh ({plug['today_runtime']}h)" +
                            (f" - {plug['today_cost']:.2f}€" if plug.get('today_cost', 0) > 0 else ""))
                lines.append(f"  Month: {plug['month_energy']}Wh ({plug['month_runtime']}h)" +
                            (f" - {plug['month_cost']:.2f}€" if plug.get('month_cost', 0) > 0 else ""))

        return "\n".join(lines)

    def _format_server_status_text(self, server: Dict, plug_status: Optional[Dict] = None) -> str:
        """Format single server status as Telegram message"""
        lines = []
        status_icon = "🟢" if server["online"] else "🔴"
        status_text = "Online" if server["online"] else "Offline"

        lines.append(f"🖥️ *{server['name']}* {status_icon}")
        lines.append("")
        lines.append(f"*Status:* {status_text}")
        lines.append(f"*Hostname:* `{server['hostname']}`")
        lines.append(f"*IP:* `{server['ip']}`")

        if server.get("mac"):
            lines.append(f"*MAC:* `{server['mac']}`")
        if server.get("plug"):
            lines.append(f"*Plug:* {server['plug']}")

        if server["online"] and server.get("uptime"):
            lines.append(f"*Uptime:* {server['uptime']}")
        elif not server["online"] and server.get("downtime"):
            lines.append(f"*Downtime:* {server['downtime']}")

        if server.get("power"):
            power = server["power"]
            lines.append("")
            lines.append("*⚡ Power:*")
            power_line = f"  Current: {power['current']}W"
            if power.get("current_cost_per_hour", 0) > 0:
                power_line += f" ({power['current_cost_per_hour']:.4f}€/h)"
            lines.append(power_line)

            lines.append(f"  Today: {power['today_energy']}Wh" +
                        (f" ({power['today_cost']:.2f}€)" if power.get('today_cost', 0) > 0 else ""))
            lines.append(f"  Month: {power['month_energy']}Wh" +
                        (f" ({power['month_cost']:.2f}€)" if power.get('month_cost', 0) > 0 else ""))

        return "\n".join(lines)

    async def _send_full_status(self, message):
        """Send full status response"""
        try:
            status = await self.status_service.get_all_status()
            text = self._format_status_text(status)

            keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data="status_refresh")]]

            await message.reply_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            await message.reply_text(f"❌ Error getting status: {str(e)}")

    async def _send_server_status(self, message, server_name: str):
        """Send single server status response"""
        server_data = self.config.get_server(server_name)

        if not server_data:
            servers = self.config.list_servers()
            server_list = "\n".join([f"• `{name}`" for name in servers.keys()]) if servers else "None"
            await message.reply_text(
                f"❌ Server '{server_name}' not found.\n\n*Available servers:*\n{server_list}",
                parse_mode="Markdown",
            )
            return

        try:
            server_status = await self.status_service.get_server_status(server_name, server_data)
            text = self._format_server_status_text(server_status)

            # Build action buttons
            keyboard = []
            if server_data.get("plug") and server_data.get("mac"):
                if server_status["online"]:
                    keyboard.append([
                        InlineKeyboardButton("🔴 Power Off", callback_data=f"confirm_off:{server_name}")
                    ])
                else:
                    keyboard.append([
                        InlineKeyboardButton("⚡ Power On", callback_data=f"power_on:{server_name}")
                    ])
            keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data=f"server:{server_name}")])

            await message.reply_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as e:
            logger.error(f"Failed to get server status: {e}")
            await message.reply_text(f"❌ Error getting server status: {str(e)}")

    async def _power_on_server_msg(self, message, server_name: str):
        """Power on server via command (with progress)"""
        server = self.config.get_server(server_name)

        if not server:
            await message.reply_text(f"❌ Server '{server_name}' not found.")
            return

        if not server.get("plug"):
            await message.reply_text(f"❌ Server '{server_name}' has no plug configured.")
            return

        if not server.get("mac"):
            await message.reply_text(
                f"❌ Cannot power on '{server_name}' - no MAC address configured.\n\n"
                f"Use CLI to add MAC address:\n"
                f"`lab server edit {server_name} --mac AA:BB:CC:DD:EE:FF`",
                parse_mode="Markdown",
            )
            return

        plug = self.config.get_plug(server["plug"])
        if not plug:
            await message.reply_text(f"❌ Plug '{server['plug']}' not found.")
            return

        # Send initial message
        status_msg = await message.reply_text(
            f"⚡ *Powering on {server_name}...*\n\n"
            f"Starting...",
            parse_mode="Markdown",
        )

        # Track progress
        logs = []
        last_update = [time.time()]

        async def progress_callback(msg: str):
            logs.append(msg)
            now = time.time()
            # Update every 2 seconds
            if now - last_update[0] >= 2:
                try:
                    progress_text = "\n".join(logs[-8:])  # Show last 8 log lines
                    await status_msg.edit_text(
                        f"⚡ *Powering on {server_name}...*\n\n"
                        f"```\n{progress_text}\n```",
                        parse_mode="Markdown",
                    )
                    last_update[0] = now
                except Exception:
                    pass

        try:
            result = await self.power_service.power_on(server, plug["ip"], progress_callback)

            if result["success"]:
                await status_msg.edit_text(
                    f"✅ *{server_name}* powered on successfully!\n\n"
                    f"Use `/status {server_name}` to check status.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 View Status", callback_data=f"server:{server_name}")]
                    ]),
                )
            else:
                progress_text = "\n".join(logs[-5:]) if logs else "No logs"
                await status_msg.edit_text(
                    f"❌ Failed to power on *{server_name}*\n\n"
                    f"{result.get('message', 'Unknown error')}\n\n"
                    f"```\n{progress_text}\n```",
                    parse_mode="Markdown",
                )
        except Exception as e:
            logger.error(f"Failed to power on server: {e}")
            await status_msg.edit_text(f"❌ Error: {str(e)}")

    async def _power_off_server_msg(self, message, server_name: str):
        """Power off server via command (with progress)"""
        server = self.config.get_server(server_name)

        if not server:
            await message.reply_text(f"❌ Server '{server_name}' not found.")
            return

        if not server.get("plug"):
            await message.reply_text(f"❌ Server '{server_name}' has no plug configured.")
            return

        plug = self.config.get_plug(server["plug"])
        if not plug:
            await message.reply_text(f"❌ Plug '{server['plug']}' not found.")
            return

        # Send initial message
        status_msg = await message.reply_text(
            f"🔴 *Powering off {server_name}...*\n\n"
            f"Initiating graceful shutdown...",
            parse_mode="Markdown",
        )

        # Track progress
        logs = []
        last_update = [time.time()]

        async def progress_callback(msg: str):
            logs.append(msg)
            now = time.time()
            # Update every 2 seconds
            if now - last_update[0] >= 2:
                try:
                    progress_text = "\n".join(logs[-8:])
                    await status_msg.edit_text(
                        f"🔴 *Powering off {server_name}...*\n\n"
                        f"```\n{progress_text}\n```",
                        parse_mode="Markdown",
                    )
                    last_update[0] = now
                except Exception:
                    pass

        try:
            result = await self.power_service.power_off(server, plug["ip"], progress_callback)

            if result["success"]:
                await status_msg.edit_text(
                    f"✅ *{server_name}* powered off successfully!",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 View Status", callback_data=f"server:{server_name}")]
                    ]),
                )
            else:
                progress_text = "\n".join(logs[-5:]) if logs else "No logs"
                await status_msg.edit_text(
                    f"⚠️ *{server_name}* powered off (with warnings)\n\n"
                    f"{result.get('message', '')}\n\n"
                    f"```\n{progress_text}\n```",
                    parse_mode="Markdown",
                )
        except Exception as e:
            logger.error(f"Failed to power off server: {e}")
            await status_msg.edit_text(f"❌ Error: {str(e)}")

    async def run(self):
        """Run the bot"""
        logger.info("Starting Telegram bot...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

        # Keep running
        while True:
            await asyncio.sleep(1)

    async def stop(self):
        """Stop the bot"""
        logger.info("Stopping Telegram bot...")
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()


async def main():
    """Main entry point for bot"""
    bot = HomelabBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
