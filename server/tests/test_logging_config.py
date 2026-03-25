"""Tests for logging_config"""

import logging

from server.logging_config import LOG_DATE_FORMAT, LOG_FORMAT, setup_logging


class TestLoggingConfig:
    """Tests for setup_logging"""

    def test_setup_logging_configures_root(self):
        """setup_logging sets root logger level and format"""
        setup_logging(logging.DEBUG)
        root = logging.getLogger()
        assert root.level == logging.DEBUG
        assert len(root.handlers) > 0

    def test_setup_logging_quiets_noisy_loggers(self):
        """Noisy third-party loggers are set to WARNING"""
        setup_logging()

        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("httpcore").level == logging.WARNING
        assert logging.getLogger("telegram").level == logging.WARNING
        assert logging.getLogger("apscheduler").level == logging.WARNING

    def test_setup_logging_idempotent(self):
        """Calling setup_logging twice doesn't duplicate handlers"""
        setup_logging()
        handler_count = len(logging.getLogger().handlers)
        setup_logging()
        assert len(logging.getLogger().handlers) == handler_count

    def test_log_format_is_string(self):
        """LOG_FORMAT is a valid format string"""
        assert "%(asctime)s" in LOG_FORMAT
        assert "%(name)s" in LOG_FORMAT
        assert "%(levelname)s" in LOG_FORMAT

    def test_log_date_format_is_string(self):
        """LOG_DATE_FORMAT is a valid date format string"""
        assert "%Y" in LOG_DATE_FORMAT
        assert "%H" in LOG_DATE_FORMAT
