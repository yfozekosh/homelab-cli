"""
Centralized logging configuration for the Homelab server.

Import and call setup_logging() once at process startup.
All modules then use logging.getLogger(__name__) as usual.
"""

import logging
import sys

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger for Docker / console output.

    Must be called once before any logging happens.
    Safe to call multiple times — only the first call takes effect
    because basicConfig is a no-op when handlers already exist.
    """
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        stream=sys.stdout,
        force=True,  # Python 3.11+: override any prior config
    )

    # Quiet down noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
