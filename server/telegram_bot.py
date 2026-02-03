"""
Telegram Bot for Homelab Management
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import List

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
            "Welcome! Use the buttons below to manage your homelab.",
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

    async def unknown_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown messages"""
        await update.message.reply_text(
            "Use /menu to see available commands.", reply_markup=self._get_main_menu()
        )

    def _get_main_menu(self) -> InlineKeyboardMarkup:
        """Get main menu keyboard"""
        keyboard = [
            [InlineKeyboardButton("🖥️ Servers", callback_data="servers")],
            [InlineKeyboardButton("🔌 Plugs", callback_data="plugs")],
        ]
        return InlineKeyboardMarkup(keyboard)

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
        """Show server details with action buttons"""
        server = self.config.get_server(server_name)

        if not server:
            await query.edit_message_text(
                f"❌ Server '{server_name}' not found.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Back", callback_data="servers")]]
                ),
            )
            return

        online = self.server_service.ping(server["hostname"])
        status = "🟢 Online" if online else "🔴 Offline"
        ip = self.server_service.resolve_hostname(server["hostname"])

        mac_display = f"`{server['mac']}`" if server.get("mac") else "⚠️ Not configured"

        text = (
            f"🖥️ *{server_name}*\n\n"
            f"Status: {status}\n"
            f"Hostname: `{server['hostname']}`\n"
            f"IP: `{ip}`\n"
            f"MAC: {mac_display}\n"
            f"Plug: {server.get('plug', 'None')}"
        )

        keyboard = []

        if server.get("plug"):
            if server.get("mac"):
                if not online:
                    keyboard.append(
                        [
                            InlineKeyboardButton(
                                "⚡ Power On", callback_data=f"power_on:{server_name}"
                            )
                        ]
                    )
                else:
                    keyboard.append(
                        [
                            InlineKeyboardButton(
                                "🔴 Power Off",
                                callback_data=f"confirm_off:{server_name}",
                            )
                        ]
                    )
            else:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            "⚠️ Cannot power on (no MAC address)", callback_data="noop"
                        )
                    ]
                )

        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="servers")])

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
        """Power on a server"""
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
            f"⚡ Powering on *{server_name}*...", parse_mode="Markdown"
        )

        # Progress callback to update message
        last_update = [0]  # Use list to allow modification in closure

        async def progress_callback(msg: str):
            import time

            now = time.time()
            if now - last_update[0] > 3:  # Update every 3 seconds
                try:
                    await query.edit_message_text(
                        f"⚡ Powering on *{server_name}*...\n\n{msg}",
                        parse_mode="Markdown",
                    )
                    last_update[0] = now
                except Exception:
                    pass  # Ignore edit errors

        try:
            result = await self.power_service.power_on(
                server, plug["ip"], progress_callback
            )

            if result["success"]:
                await query.edit_message_text(
                    f"✅ *{server_name}* powered on successfully!",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "⬅️ Back to Servers", callback_data="servers"
                                )
                            ]
                        ]
                    ),
                )
            else:
                await query.edit_message_text(
                    f"❌ Failed to power on *{server_name}*\n\n{result['message']}",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "⬅️ Back to Servers", callback_data="servers"
                                )
                            ]
                        ]
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to power on server: {e}")
            await query.edit_message_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ Back to Servers", callback_data="servers"
                            )
                        ]
                    ]
                ),
            )

    async def _power_off_server(self, query, server_name: str):
        """Power off a server"""
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
            f"🔴 Powering off *{server_name}*...", parse_mode="Markdown"
        )

        # Progress callback
        last_update = [0]

        async def progress_callback(msg: str):
            import time

            now = time.time()
            if now - last_update[0] > 3:
                try:
                    await query.edit_message_text(
                        f"🔴 Powering off *{server_name}*...\n\n{msg}",
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
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "⬅️ Back to Servers", callback_data="servers"
                                )
                            ]
                        ]
                    ),
                )
            else:
                await query.edit_message_text(
                    f"⚠️ *{server_name}* powered off (with warnings)\n\n{result['message']}",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "⬅️ Back to Servers", callback_data="servers"
                                )
                            ]
                        ]
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to power off server: {e}")
            await query.edit_message_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ Back to Servers", callback_data="servers"
                            )
                        ]
                    ]
                ),
            )

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
