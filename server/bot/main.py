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
from telegram.error import (
    TimedOut,
    NetworkError,
    Forbidden,
    BadRequest,
    RetryAfter,
    Conflict,
    InvalidToken,
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

        # Initialize handlers (pass self reference for tracked tasks)
        self.handlers = BotHandlers(self.container, self.allowed_users, bot=self)
        self.handlers.register_listeners()

        # Track broadcast failures for health monitoring
        self.broadcast_failures: int = 0
        self.max_broadcast_failures: int = 10

        # Track background tasks for cleanup
        self._background_tasks: set = set()

        # Last successful activity timestamp
        self.last_activity: float = time.time()

        # Token validation state
        self.token_valid: bool = True

        # Build application with robust connection pooling
        self.app = (
            Application.builder()
            .token(self.token)
            .connection_pool_size(8)
            .read_timeout(30)
            .connect_timeout(30)
            .write_timeout(30)
            .pool_timeout(10)
            .get_updates_connection_pool_size(4)
            .get_updates_read_timeout(60)
            .build()
        )
        self._setup_handlers()
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        """Setup event listeners for notifications with timeout protection"""
        event_service = self.container.event_service
        # Wrap handlers with timeout to prevent blocking
        event_service.add_listener("deployment.started", self._wrap_with_timeout(self._on_deployment_started, "deployment.started"))
        event_service.add_listener(
            "deployment.completed", self._wrap_with_timeout(self._on_deployment_completed, "deployment.completed")
        )
        event_service.add_listener("deployment.failed", self._wrap_with_timeout(self._on_deployment_failed, "deployment.failed"))
        event_service.add_listener(
            "server.status_change", self._wrap_with_timeout(self._on_server_status_change, "server.status_change")
        )

    def _wrap_with_timeout(self, coro_func, event_name: str):
        """Wrap a coroutine with a timeout to prevent blocking"""
        async def wrapped(data: dict):
            try:
                await asyncio.wait_for(coro_func(data), timeout=30.0)
            except asyncio.TimeoutError:
                logger.error(f"Event handler {event_name} timed out after 30s")
            except Exception as e:
                logger.error(f"Event handler {event_name} failed: {e}")
        return wrapped

    def create_tracked_task(self, coro):
        """Create a task and track it for cleanup"""
        task = asyncio.create_task(coro)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return task

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
        """Send a message to all allowed users with comprehensive error handling"""
        if not self.allowed_users:
            logger.warning("No allowed users configured for broadcast")
            return

        sent_count = 0
        for user_id in self.allowed_users:
            try:
                await self.app.bot.send_message(
                    chat_id=user_id, text=message, parse_mode=parse_mode
                )
                logger.debug(f"Broadcast message sent to {user_id}")
                sent_count += 1
                self.broadcast_failures = 0  # Reset on success
                self.last_activity = time.time()
            except InvalidToken as e:
                # Token is invalid - critical error
                logger.error(f"Invalid token: {e}")
                self.token_valid = False
                self.broadcast_failures += 1
            except Forbidden as e:
                # Bot was blocked by user or chat not found
                logger.error(f"Forbidden (bot blocked or chat not found) for user {user_id}: {e}")
                self.broadcast_failures += 1
            except RetryAfter as e:
                # Rate limited - wait and retry
                logger.warning(f"Rate limited for user {user_id}, waiting {e.retry_after}s")
                await asyncio.sleep(e.retry_after)
                try:
                    await self.app.bot.send_message(
                        chat_id=user_id, text=message, parse_mode=parse_mode
                    )
                    sent_count += 1
                    self.broadcast_failures = 0
                except Exception as retry_error:
                    logger.error(f"Retry failed for user {user_id}: {retry_error}")
                    self.broadcast_failures += 1
            except (TimedOut, NetworkError) as e:
                # Network issues - may recover
                logger.warning(f"Network error sending to user {user_id}: {e}")
                self.broadcast_failures += 1
            except BadRequest as e:
                # Invalid message content
                logger.error(f"Bad request (invalid message content) for user {user_id}: {e}")
                self.broadcast_failures += 1
            except Exception as e:
                logger.error(f"Unexpected error sending to user {user_id}: {e}", exc_info=True)
                self.broadcast_failures += 1

        # Log health status
        if sent_count == 0 and self.broadcast_failures > 0:
            logger.warning(f"Broadcast failed: 0/{len(self.allowed_users)} messages sent, {self.broadcast_failures} total failures")
        elif self.broadcast_failures >= self.max_broadcast_failures:
            logger.error(f"CRITICAL: {self.broadcast_failures} consecutive broadcast failures - bot may be unhealthy")

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
        """Run the bot with automatic recovery from connection issues"""
        logger.info("Initializing Telegram bot...")
        logger.info("Allowed users: %d configured", len(self.allowed_users))

        max_retries = 3
        retry_count = 0
        token_check_interval = 300  # Check token validity every 5 minutes
        last_token_check = time.time()

        while retry_count < max_retries:
            try:
                await self.app.initialize()
                logger.info("Telegram bot application initialized")

                if self.app.updater:
                    await self.app.updater.start_polling()
                    logger.info("Telegram bot polling started")

                    # Send startup message to allowed users
                    if self.allowed_users:
                        await self._send_startup_message()

                    # Main loop with health monitoring
                    while True:
                        await asyncio.sleep(30)
                        retry_count = 0  # Reset on successful cycle
                        self.last_activity = time.time()

                        # Write heartbeat file for health check endpoint
                        await self._write_heartbeat()

                        # Periodic token validation
                        current_time = time.time()
                        if current_time - last_token_check > token_check_interval:
                            await self._validate_token()
                            last_token_check = current_time

                        # Check for critical failures
                        if not self.token_valid:
                            logger.error("Token marked as invalid - exiting to allow restart")
                            raise InvalidToken("Token invalid")

                        if self.broadcast_failures >= self.max_broadcast_failures:
                            logger.error("Too many broadcast failures - exiting to allow restart")
                            raise Exception("Too many broadcast failures")
                else:
                    logger.warning("Telegram bot updater not available")
                    break

            except InvalidToken as e:
                # Token is invalid - no point retrying
                logger.error(f"Telegram token is invalid: {e}")
                raise
            except Conflict as e:
                # Another bot instance is running
                logger.error(f"Conflict (another bot instance running): {e}")
                retry_count += 1
                if retry_count < max_retries:
                    logger.info("Retrying in case of transient conflict...")
                    await asyncio.sleep(10)
                    continue
                raise
            except (TimedOut, NetworkError) as e:
                retry_count += 1
                logger.warning(f"Network error (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    logger.info("Attempting to reconnect...")
                    await asyncio.sleep(5)
                    # Try to recover by reinitializing
                    try:
                        if self.app.updater:
                            await self.app.updater.stop()
                        await self.app.shutdown()
                    except Exception:
                        pass
                    continue
                else:
                    logger.error("Max retries reached, exiting to allow restart")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                raise

    async def _send_startup_message(self):
        """Send startup message to all allowed users"""
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

        for user_id in self.allowed_users:
            try:
                await self.app.bot.send_message(
                    chat_id=user_id, text=message_text, parse_mode="Markdown"
                )
                self.last_activity = time.time()
            except Exception as e:
                logger.error(f"Failed to send startup message to {user_id}: {e}")

    async def _validate_token(self):
        """Validate the bot token by calling getMe"""
        try:
            bot_info = await self.app.bot.get_me()
            if bot_info:
                self.token_valid = True
                logger.debug(f"Token validation successful: @{bot_info.username}")
        except InvalidToken as e:
            logger.error(f"Token validation failed (InvalidToken): {e}")
            self.token_valid = False
        except Exception as e:
            logger.warning(f"Token validation encountered error (may be transient): {e}")
            # Don't mark as invalid on network errors

    async def _write_heartbeat(self):
        """Write heartbeat file for health check endpoint"""
        import os
        import json
        
        try:
            heartbeat_file = "/app/data/bot_heartbeat.json"
            heartbeat_data = {
                "timestamp": time.time(),
                "last_activity": self.last_activity,
                "token_valid": self.token_valid,
                "broadcast_failures": self.broadcast_failures,
                "allowed_users": len(self.allowed_users)
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(heartbeat_file), exist_ok=True)
            
            # Write atomically using temp file
            temp_file = heartbeat_file + ".tmp"
            with open(temp_file, "w") as f:
                json.dump(heartbeat_data, f)
            os.replace(temp_file, heartbeat_file)
            
            logger.debug("Heartbeat written successfully")
        except Exception as e:
            logger.error(f"Failed to write heartbeat: {e}")

    async def stop(self):
        """Stop the bot and clean up background tasks"""
        logger.info("Stopping Telegram bot...")
        
        # Cancel all background tasks
        if self._background_tasks:
            logger.info(f"Cancelling {len(self._background_tasks)} background task(s)")
            for task in self._background_tasks:
                task.cancel()
            # Wait for tasks to complete cancellation
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
            self._background_tasks.clear()
        
        if self.app.updater:
            await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
        logger.info("Telegram bot stopped")


async def main():
    """Main entry point for bot"""
    bot = HomelabBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
