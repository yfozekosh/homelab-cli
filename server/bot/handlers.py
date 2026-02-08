import logging
import asyncio
import time
from typing import List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..dependencies import ServiceContainer
from .keyboards import get_main_menu, get_back_menu_button
from .formatters import (
    format_status_text, 
    format_server_status_text, 
    format_plug_status_text,
    format_short_status,
    format_servers_summary,
    format_plugs_summary,
)

logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self, container: ServiceContainer, allowed_users: List[int]):
        self.config = container.config
        self.plug_service = container.plug_service
        self.server_service = container.server_service
        self.power_service = container.power_service
        self.status_service = container.status_service
        self.allowed_users = allowed_users

    def _check_access(self, user_id: int) -> bool:
        """Check if user has access"""
        if not self.allowed_users:
            logger.warning("No user IDs configured. Allowing all users.")
            return True
        return user_id in self.allowed_users

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if not update.effective_user or not update.message:
            return
        
        user_id = update.effective_user.id

        if not self._check_access(user_id):
            await update.message.reply_text(
                "❌ Access denied. Your user ID is not authorized.\n"
                f"Your ID: {user_id}"
            )
            return

        # Reload config to get latest changes
        self.config.reload()

        # Get quick status
        try:
            status = await self.status_service.get_all_status()
            status_text = format_short_status(status)
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            status_text = "📊 *Quick Status:* (Unable to load)"

        await update.message.reply_text(
            "🏠 *Homelab Management Bot*\n\n"
            f"{status_text}\n\n"
            "*Commands:*\n"
            "`/status` - Full status overview\n"
            "`/status <server>` - Server details\n"
            "`/on <server>` - Power on server\n"
            "`/off <server>` - Power off server\n"
            "`/servers` - List servers\n"
            "`/plugs` - List plugs\n"
            "`/menu` - Show menu\n"
            "`/clear` - Clear chat",
            parse_mode="Markdown",
            reply_markup=get_main_menu(),
        )

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command"""
        if not update.effective_user or not update.message:
            return
        
        user_id = update.effective_user.id

        if not self._check_access(user_id):
            await update.message.reply_text("❌ Access denied.")
            return

        # Reload config to get latest changes
        self.config.reload()

        # Get quick status
        try:
            status = await self.status_service.get_all_status()
            status_text = format_short_status(status)
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            status_text = "📊 *Quick Status:* (Unable to load)"

        await update.message.reply_text(
            f"🏠 *Main Menu*\n\n{status_text}",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

    async def servers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /servers command"""
        if not update.effective_user or not update.message:
            return
        
        user_id = update.effective_user.id

        if not self._check_access(user_id):
            await update.message.reply_text("❌ Access denied.")
            return

        servers = self.config.list_servers()

        if not servers:
            await update.message.reply_text("No servers configured.")
            return
        
        status_msg = await update.message.reply_text("⏳ *Checking servers...*", parse_mode="Markdown")

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

        await status_msg.edit_text(
            "🖥️ *Servers:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    async def plugs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /plugs command"""
        if not update.effective_user or not update.message:
            return
        
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
        if not update.effective_user or not update.message:
            return
        
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
        if not update.effective_user or not update.message:
            return
        
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

    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command - clear chat history"""
        if not update.effective_user or not update.message:
            return
        
        user_id = update.effective_user.id

        if not self._check_access(user_id):
            await update.message.reply_text("❌ Access denied.")
            return

        # Send multiple newlines to push messages up
        clear_text = "\n" * 50
        await update.message.reply_text(
            f"{clear_text}🧹 *Chat cleared*\n\nUse /menu to continue.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

    async def off_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /off <server_name> command"""
        if not update.effective_user or not update.message:
            return
        
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
        if not query or not query.from_user or not query.data:
            return
        
        user_id = query.from_user.id

        if not self._check_access(user_id):
            await query.answer("❌ Access denied.", show_alert=True)
            return

        await query.answer()

        data = query.data

        if data == "menu":
            # Reload config to get latest changes
            self.config.reload()
            
            # Get quick status for menu
            try:
                status = await self.status_service.get_all_status()
                status_text = format_short_status(status)
            except Exception as e:
                logger.error(f"Failed to get status: {e}")
                status_text = "📊 *Quick Status:* (Unable to load)"
            
            await query.edit_message_text(
                f"🏠 *Main Menu*\n\n{status_text}",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )

        elif data == "servers":
            await self._show_servers_list(query)

        elif data == "plugs":
            await self._show_plugs_list(query)

        elif data.startswith("server:"):
            server_name = data.split(":", 1)[1]
            await self._show_server_details(query, server_name)

        elif data.startswith("plug:"):
            plug_name = data.split(":", 1)[1]
            await self._show_plug_details(query, plug_name)

        elif data.startswith("plug_on:"):
            plug_name = data.split(":", 1)[1]
            await self._toggle_plug(query, plug_name, "on")

        elif data.startswith("plug_off:"):
            plug_name = data.split(":", 1)[1]
            await self._toggle_plug(query, plug_name, "off")

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
        if not update.message:
            return
        
        await update.message.reply_text(
            "Use /menu to see available commands.", reply_markup=get_main_menu()
        )

    # --- Helper methods ---

    async def _refresh_status(self, query):
        """Refresh and show full status"""
        await query.edit_message_text(
            "⏳ *Refreshing status...*",
            parse_mode="Markdown"
        )
        try:
            status = await self.status_service.get_all_status()
            text = format_status_text(status)

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
        """Show servers list with status summary and buttons"""
        servers = self.config.list_servers()

        if not servers:
            await query.edit_message_text(
                "No servers configured.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Back", callback_data="menu")]]
                ),
            )
            return

        await query.edit_message_text(
            "⏳ *Checking servers...*",
            parse_mode="Markdown"
        )

        # Get status for all servers
        servers_status = []
        try:
            status = await self.status_service.get_all_status()
            servers_status = status.get("servers", [])
            summary_text = format_servers_summary(servers_status)
        except Exception as e:
            logger.error(f"Failed to get servers status: {e}")
            # Fallback to simple ping check
            servers_status = []
            for name, server in servers.items():
                online = self.server_service.ping(server["hostname"])
                servers_status.append({"name": name, "online": online})
            summary_text = format_servers_summary(servers_status)

        keyboard = []
        for server_info in servers_status:
            status_icon = "🟢" if server_info.get("online") else "🔴"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{status_icon} {server_info['name']}", 
                        callback_data=f"server:{server_info['name']}"
                    )
                ]
            )

        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu")])

        await query.edit_message_text(
            summary_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    async def _show_plugs_list(self, query):
        """Show plugs list with status summary and buttons"""
        plugs = self.config.list_plugs()

        if not plugs:
            await query.edit_message_text(
                "No plugs configured.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Back", callback_data="menu")]]
                ),
            )
            return

        await query.edit_message_text(
            "⏳ *Checking plugs...*",
            parse_mode="Markdown"
        )
        
        # Get status for all plugs
        plugs_status = []
        try:
            status = await self.status_service.get_all_status()
            plugs_status = status.get("plugs", [])
            summary_text = format_plugs_summary(plugs_status)
        except Exception as e:
            logger.error(f"Failed to get plugs status: {e}")
            # Fallback to simple list
            plugs_status = [{"name": name, "online": False} for name in plugs.keys()]
            summary_text = format_plugs_summary(plugs_status)
        
        keyboard = []
        for plug_info in plugs_status:
            if not plug_info.get("online"):
                icon = "🔴"
            elif plug_info.get("state") == "on":
                icon = "⚡"
            else:
                icon = "⭕"
            
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{icon} {plug_info['name']}", 
                        callback_data=f"plug:{plug_info['name']}"
                    )
                ]
            )

        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu")])

        await query.edit_message_text(
            summary_text,
            parse_mode="Markdown", 
            reply_markup=InlineKeyboardMarkup(keyboard)
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

        await query.edit_message_text(
            f"⏳ *Loading details for {server_name}...*",
            parse_mode="Markdown"
        )

        try:
            server_status = await self.status_service.get_server_status(server_name, server_data)
            text = format_server_status_text(server_status)

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

    async def _show_plug_details(self, query, plug_name: str):
        """Show plug details with actions"""
        plug_data = self.config.get_plug(plug_name)
        
        if not plug_data:
            await query.edit_message_text(
                f"❌ Plug '{plug_name}' not found.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Back", callback_data="plugs")]]
                ),
            )
            return

        await query.edit_message_text(
            f"⏳ *Loading details for {plug_name}...*",
            parse_mode="Markdown"
        )

        try:
            plug_status = await self.status_service.get_plug_status(plug_name, plug_data)
            text = format_plug_status_text(plug_status)

            keyboard = []
            
            if plug_status.get("online"):
                if plug_status["state"] == "on":
                    keyboard.append([
                        InlineKeyboardButton("⭕ Turn Off", callback_data=f"plug_off:{plug_name}")
                    ])
                else:
                    keyboard.append([
                        InlineKeyboardButton("⚡ Turn On", callback_data=f"plug_on:{plug_name}")
                    ])
            
            keyboard.append([
                InlineKeyboardButton("🔄 Refresh", callback_data=f"plug:{plug_name}"),
                InlineKeyboardButton("⬅️ Back", callback_data="plugs"),
            ])

            await query.edit_message_text(
                text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Failed to get plug details: {e}")
            await query.edit_message_text(
                f"❌ Error getting plug details: {str(e)}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Back", callback_data="plugs")]]
                )
            )

    async def _toggle_plug(self, query, plug_name: str, action: str):
        """Toggle plug power state"""
        plug_data = self.config.get_plug(plug_name)
        
        if not plug_data:
            await query.answer(f"Plug '{plug_name}' not found.", show_alert=True)
            return

        # Acknowledge button press
        await query.answer(f"Turning {action} {plug_name}...")
        
        action_text = "Turning ON" if action == "on" else "Turning OFF"
        await query.edit_message_text(
            f"⏳ *{action_text} {plug_name}...*",
            parse_mode="Markdown"
        )
        
        try:
            if action == "on":
                await self.plug_service.turn_on(plug_data["ip"])
            else:
                await self.plug_service.turn_off(plug_data["ip"])
                
            # Wait a moment for state to change
            await asyncio.sleep(1)
            
            # Refresh details
            await self._show_plug_details(query, plug_name)
            
        except Exception as e:
            logger.error(f"Failed to toggle plug: {e}")
            await query.edit_message_text(
                f"❌ Error toggling plug: {str(e)}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Back", callback_data=f"plug:{plug_name}")]
                ])
            )

    async def _send_full_status(self, message):
        """Send full status response"""
        status_msg = await message.reply_text("⏳ *Loading status...*", parse_mode="Markdown")
        try:
            status = await self.status_service.get_all_status()
            text = format_status_text(status)

            keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data="status_refresh")]]

            await status_msg.edit_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            await status_msg.edit_text(f"❌ Error getting status: {str(e)}")

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

        status_msg = await message.reply_text(f"⏳ *Loading details for {server_name}...*", parse_mode="Markdown")

        try:
            server_status = await self.status_service.get_server_status(server_name, server_data)
            text = format_server_status_text(server_status)

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

            await status_msg.edit_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as e:
            logger.error(f"Failed to get server status: {e}")
            await status_msg.edit_text(f"❌ Error getting server status: {str(e)}")

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
