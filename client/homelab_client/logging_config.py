"""Logging configuration for Homelab client"""

import logging
import sys
from typing import Optional


class EmojiFormatter(logging.Formatter):
    """Custom formatter that preserves emoji output for console"""

    LEVEL_EMOJIS = {
        logging.DEBUG: "🔍",
        logging.INFO: "ℹ️ ",
        logging.WARNING: "⚠️ ",
        logging.ERROR: "❌",
        logging.CRITICAL: "💀",
    }

    def format(self, record: logging.LogRecord) -> str:
        emoji = self.LEVEL_EMOJIS.get(record.levelno, "")
        record.emoji = emoji
        return super().format(record)


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    verbose: bool = False
) -> logging.Logger:
    """Set up logging for the Homelab client
    
    Args:
        level: Logging level (default: INFO)
        log_file: Optional file path to write logs
        verbose: If True, use DEBUG level
        
    Returns:
        Configured logger instance
    """
    if verbose:
        level = logging.DEBUG

    logger = logging.getLogger("homelab")
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()

    # Console handler with emoji support
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_formatter = EmojiFormatter(
        "%(emoji)s %(message)s" if level >= logging.INFO else "%(emoji)s [%(name)s] %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "homelab") -> logging.Logger:
    """Get a logger instance
    
    Args:
        name: Logger name (default: "homelab")
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
