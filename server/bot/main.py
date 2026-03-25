"""
Telegram Bot for Homelab Management
"""

import asyncio
import logging
import os
import re
import time
from typing import List

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from ..dependencies import get_service_container
from ..logging_config import setup_logging
from .handlers import BotHandlers

# Setup logging (must happen before any getLogger calls)
setup_logging()
logger = logging.getLogger(__name__)


def escape_markdown_v2(text: str) -> str:
    """Escape Telegram MarkdownV2 special characters."""
    if not text:
        return ""

    # Escape backslash first to avoid interfering with later substitutions.
    text = text.replace("\\", "\\\\")

    return re.sub(r"([_*\[\]()~`>#+\-=|{}.!])", r"\\\1", text)


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

        # Initialize services via Dependency Injection
        self.container = get_service_container()

        # Initialize handlers
        self.handlers = BotHandlers(self.container, self.allowed_users)
        self.handlers.register_listeners()

        # Build application
        self.app = Application.builder().token(self.token).build()
        self._setup_handlers()
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        """Setup event listeners for notifications"""
        event_service = self.container.event_service
        event_service.add_listener("deployment.started", self._on_deployment_started)
        event_service.add_listener(
            "deployment.completed", self._on_deployment_completed
        )
        event_service.add_listener("deployment.failed", self._on_deployment_failed)
        event_service.add_listener(
            "server.status_change", self._on_server_status_change
        )

    async def _on_deployment_started(self, data: dict):
        """Handle deployment started event"""
        message = "🚀 *Deployment Started*\n\n"
        if data.get("commit"):
            message += f"📝 Commit: `{data['commit'][:7]}`\n"
        if data.get("message"):
            message += f"💬 Message: {data['message']}\n"
        if data.get("branch"):
            message += f"🌿 Branch: {data['branch']}\n"
        message += "\n⏳ Deploying updates..."
        await self.broadcast_message(message)

    async def _on_deployment_completed(self, data: dict):
        """Handle deployment completed event"""
        message = "✅ *Deployment Completed*\n\n"
        if data.get("duration"):
            message += f"⏱️ Duration: {data['duration']}\n"
        message += "\nBot restarted successfully!"
        await self.broadcast_message(message)

    async def _on_deployment_failed(self, data: dict):
        """Handle deployment failed event"""
        message = "❌ *Deployment Failed*\n\n"
        if data.get("error"):
            message += f"Error: {data['error']}\n"
        await self.broadcast_message(message)

    async def _on_server_status_change(self, data: dict):
        """Handle server status change event"""
        server_name = data.get("server", "Unknown")
        old_status = data.get("old_status", "unknown")
        new_status = data.get("new_status", "unknown")

        icon = "🟢" if new_status == "online" else "🔴"
        message = f"{icon} *Server Status Change*\n\n"
        message += f"Server: *{server_name}*\n"
        message += f"Status: {old_status} → {new_status}"
        await self.broadcast_message(message)

    async def broadcast_message(self, message: str, parse_mode: str = "Markdown"):
        """Send a message to all allowed users"""
        if not self.allowed_users:
            logger.warning("No allowed users configured for broadcast")
            return

        for user_id in self.allowed_users:
            try:
                await self.app.bot.send_message(
                    chat_id=user_id, text=message, parse_mode=parse_mode
                )
                logger.debug(f"Broadcast message sent to {user_id}")
            except Exception as e:
                logger.error(f"Failed to send broadcast to {user_id}: {e}")

    def _setup_handlers(self):
        """Setup command and callback handlers"""
        self.app.add_handler(CommandHandler("start", self.handlers.start_command))
        self.app.add_handler(CommandHandler("menu", self.handlers.menu_command))
        self.app.add_handler(CommandHandler("servers", self.handlers.servers_command))
        self.app.add_handler(CommandHandler("plugs", self.handlers.plugs_command))
        self.app.add_handler(CommandHandler("status", self.handlers.status_command))
        self.app.add_handler(CommandHandler("on", self.handlers.on_command))
        self.app.add_handler(CommandHandler("off", self.handlers.off_command))
        self.app.add_handler(CommandHandler("clear", self.handlers.clear_command))
        self.app.add_handler(CallbackQueryHandler(self.handlers.button_callback))
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, self.handlers.unknown_message
            )
        )

    async def run(self):
        """Run the bot"""
        logger.info("Initializing Telegram bot...")
        logger.info("Allowed users: %d configured", len(self.allowed_users))
        await self.app.initialize()
        logger.info("Telegram bot application initialized")
        await self.app.start()
        if self.app.updater:
            await self.app.updater.start_polling()
            logger.info("Telegram bot polling started")
        else:
            logger.warning("Telegram bot updater not available")

        # Send startup message to allowed users
        if self.allowed_users:
            # Load build info
            build_info = {}
            try:
                import json

                # Try relative to module first, then absolute
                paths = ["server/build_info.json", "build_info.json"]
                for path in paths:
                    if os.path.exists(path):
                        with open(path, "r") as f:
                            build_info = json.load(f)
                        break
            except Exception as e:
                logger.warning(f"Failed to load build info: {e}")

            message_text = "🚀 *Homelab Bot Deployed and Ready!*\n\n"

            if build_info:
                message_text += (
                    f"📅 *Build Date:* {build_info.get('build_date', 'Unknown')}\n"
                )
                message_text += (
                    f"📅 *Commit Date:* {build_info.get('commit_date', 'Unknown')}\n"
                )
                message_text += (
                    f"🔖 *Commit:* `{build_info.get('commit_sha', 'Unknown')[:7]}`\n"
                )
                message_text += (
                    f"📝 *Message:* {build_info.get('commit_message', 'Unknown')}\n"
                )

                if build_info.get("latest_changes"):
                    message_text += f"\n📋 *Latest Changes:*\n```\n{build_info['latest_changes']}\n```"

                message_text += "/start\n"

            for user_id in self.allowed_users:
                try:
                    await self.app.bot.send_message(
                        chat_id=user_id, text=message_text, parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Failed to send startup message to {user_id}: {e}")

        # Keep running
        while True:
            await asyncio.sleep(1)

    async def stop(self):
        """Stop the bot"""
        logger.info("Stopping Telegram bot...")
        if self.app.updater:
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
