"""Unit tests for server constants module"""

import pytest
from server.constants import (
    DEFAULT_TIMEOUT,
    SHORT_TIMEOUT,
    LONG_TIMEOUT,
    SSH_TIMEOUT,
    PING_TIMEOUT,
    PLUG_TIMEOUT,
    POWER_CHECK_INTERVAL,
    POWER_ON_MAX_WAIT,
    POWER_OFF_MAX_WAIT,
    POWER_THRESHOLD_WATTS,
    WOL_RETRY_COUNT,
    WOL_RETRY_INTERVAL,
    MAX_NAME_LENGTH,
    MAX_HOSTNAME_LENGTH,
    MAX_ELECTRICITY_PRICE,
    SSE_KEEPALIVE_INTERVAL,
)


class TestTimeoutConstants:
    """Tests for timeout-related constants"""

    def test_default_timeout_is_positive(self):
        assert DEFAULT_TIMEOUT > 0

    def test_short_timeout_is_positive(self):
        assert SHORT_TIMEOUT > 0

    def test_long_timeout_is_positive(self):
        assert LONG_TIMEOUT > 0

    def test_ssh_timeout_is_positive(self):
        assert SSH_TIMEOUT > 0

    def test_ping_timeout_is_positive(self):
        assert PING_TIMEOUT > 0

    def test_plug_timeout_is_positive(self):
        assert PLUG_TIMEOUT > 0

    def test_timeout_ordering(self):
        """Short < Default < Long"""
        assert SHORT_TIMEOUT < DEFAULT_TIMEOUT
        assert DEFAULT_TIMEOUT < LONG_TIMEOUT

    def test_ssh_timeout_reasonable(self):
        """SSH timeout should be between 1 and 60 seconds"""
        assert 1 <= SSH_TIMEOUT <= 60

    def test_ping_timeout_reasonable(self):
        """Ping timeout should be between 1 and 30 seconds"""
        assert 1 <= PING_TIMEOUT <= 30


class TestPowerConstants:
    """Tests for power control constants"""

    def test_power_check_interval_is_positive(self):
        assert POWER_CHECK_INTERVAL > 0

    def test_power_on_max_wait_is_positive(self):
        assert POWER_ON_MAX_WAIT > 0

    def test_power_off_max_wait_is_positive(self):
        assert POWER_OFF_MAX_WAIT > 0

    def test_power_threshold_is_non_negative(self):
        assert POWER_THRESHOLD_WATTS >= 0


class TestRetryConstants:
    """Tests for retry-related constants"""

    def test_wol_retry_count_is_positive(self):
        assert WOL_RETRY_COUNT > 0

    def test_wol_retry_interval_is_positive(self):
        assert WOL_RETRY_INTERVAL > 0

    def test_wol_retry_count_is_integer(self):
        assert isinstance(WOL_RETRY_COUNT, int)


class TestValidationConstants:
    """Tests for validation limit constants"""

    def test_max_name_length_is_positive(self):
        assert MAX_NAME_LENGTH > 0

    def test_max_hostname_length_is_positive(self):
        assert MAX_HOSTNAME_LENGTH > 0

    def test_max_electricity_price_is_positive(self):
        assert MAX_ELECTRICITY_PRICE > 0

    def test_hostname_length_reasonable(self):
        """RFC 1035: max 253 characters for FQDN"""
        assert MAX_HOSTNAME_LENGTH == 253

    def test_name_length_reasonable(self):
        """DNS label: max 63 characters"""
        assert MAX_NAME_LENGTH == 63


class TestSSEConstants:
    """Tests for SSE streaming constants"""

    def test_sse_keepalive_interval_is_positive(self):
        assert SSE_KEEPALIVE_INTERVAL > 0


class TestConstantTypes:
    """Tests that constants have expected types"""

    def test_all_timeouts_are_numeric(self):
        assert isinstance(DEFAULT_TIMEOUT, (int, float))
        assert isinstance(SHORT_TIMEOUT, (int, float))
        assert isinstance(LONG_TIMEOUT, (int, float))
        assert isinstance(SSH_TIMEOUT, (int, float))
        assert isinstance(PING_TIMEOUT, (int, float))
        assert isinstance(PLUG_TIMEOUT, (int, float))

    def test_power_constants_are_numeric(self):
        assert isinstance(POWER_CHECK_INTERVAL, (int, float))
        assert isinstance(POWER_ON_MAX_WAIT, (int, float))
        assert isinstance(POWER_OFF_MAX_WAIT, (int, float))
        assert isinstance(POWER_THRESHOLD_WATTS, (int, float))

    def test_max_values_are_numeric(self):
        assert isinstance(MAX_NAME_LENGTH, int)
        assert isinstance(MAX_HOSTNAME_LENGTH, int)
        assert isinstance(MAX_ELECTRICITY_PRICE, (int, float))
