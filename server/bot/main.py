"""
Telegram Bot for Homelab Management
"""

import os
import logging
import asyncio
from typing import List

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from ..dependencies import get_service_container
from .handlers import BotHandlers

# Configure logging
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

        # Initialize services via Dependency Injection
        self.container = get_service_container()
        
        # Initialize handlers
        self.handlers = BotHandlers(self.container, self.allowed_users)

        # Build application
        self.app = Application.builder().token(self.token).build()
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup command and callback handlers"""
        self.app.add_handler(CommandHandler("start", self.handlers.start_command))
        self.app.add_handler(CommandHandler("menu", self.handlers.menu_command))
        self.app.add_handler(CommandHandler("servers", self.handlers.servers_command))
        self.app.add_handler(CommandHandler("plugs", self.handlers.plugs_command))
        self.app.add_handler(CommandHandler("status", self.handlers.status_command))
        self.app.add_handler(CommandHandler("on", self.handlers.on_command))
        self.app.add_handler(CommandHandler("off", self.handlers.off_command))
        self.app.add_handler(CallbackQueryHandler(self.handlers.button_callback))
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.unknown_message)
        )

    async def run(self):
        """Run the bot"""
        logger.info("Starting Telegram bot...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

        # Send startup message to allowed users
        if self.allowed_users:
            for user_id in self.allowed_users:
                try:
                    await self.app.bot.send_message(
                        chat_id=user_id,
                        text="🚀 Homelab Bot Deployed and Ready!"
                    )
                except Exception as e:
                    logger.error(f"Failed to send startup message to {user_id}: {e}")

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
