"""Unit tests for StatusService"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from server.status_service import StatusService


@pytest.fixture
def config():
    """Mock Config with in-memory data"""
    cfg = MagicMock()
    cfg.data = {
        "plugs": {
            "plug1": {"ip": "192.168.1.100"},
            "plug2": {"ip": "192.168.1.101"},
        },
        "servers": {
            "srv1": {"hostname": "server1.local", "mac": "AA:BB:CC:DD:EE:01", "plug": "plug1"},
            "srv2": {"hostname": "server2.local", "mac": "AA:BB:CC:DD:EE:02", "plug": None},
        },
        "settings": {"electricity_price": 0.25},
    }
    cfg.list_plugs.return_value = cfg.data["plugs"]
    cfg.list_servers.return_value = cfg.data["servers"]
    cfg.get_plug.side_effect = lambda name: cfg.data["plugs"].get(name)
    cfg.get_server.side_effect = lambda name: cfg.data["servers"].get(name)
    cfg.get_electricity_price.return_value = 0.25
    cfg.get_server_state.return_value = None
    cfg.update_server_state.return_value = None
    return cfg


@pytest.fixture
def plug_service():
    """Mock PlugService"""
    svc = AsyncMock()
    svc.get_full_status.return_value = {
        "on": True,
        "signal_level": 3,
        "current_power": 50.0,
        "today_runtime": 120,
        "today_energy": 500.0,
        "month_runtime": 3600,
        "month_energy": 15000.0,
    }
    return svc


@pytest.fixture
def server_service():
    """Mock ServerService"""
    svc = AsyncMock()
    svc.ping_async.return_value = True
    svc.resolve_hostname_async.return_value = "192.168.1.50"
    return svc


@pytest.fixture
def status_service(config, plug_service, server_service):
    """StatusService with mocked dependencies"""
    return StatusService(config, plug_service, server_service)


class TestFormatDuration:
    """Tests for _format_duration"""

    def test_days_hours_minutes(self, status_service):
        """Formats days, hours, and minutes"""
        past = (datetime.now(timezone.utc) - timedelta(days=2, hours=3, minutes=15)).isoformat()
        result = status_service._format_duration(past)
        assert "2d" in result
        assert "3h" in result
        assert "15m" in result

    def test_minutes_only(self, status_service):
        """Formats minutes only for short durations"""
        past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        result = status_service._format_duration(past)
        assert "5m" in result
        assert "d" not in result
        assert "h" not in result

    def test_hours_no_days(self, status_service):
        """Formats hours without days"""
        past = (datetime.now(timezone.utc) - timedelta(hours=7)).isoformat()
        result = status_service._format_duration(past)
        assert "7h" in result
        assert "d" not in result

    def test_invalid_timestamp_returns_unknown(self, status_service):
        """Returns 'unknown' for invalid timestamp"""
        result = status_service._format_duration("not-a-timestamp")
        assert result == "unknown"


class TestGetPlugStatus:
    """Tests for get_plug_status"""

    @pytest.mark.asyncio
    async def test_online_plug_returns_full_data(self, status_service, plug_service):
        """Returns detailed status for online plug"""
        result = await status_service.get_plug_status("plug1", {"ip": "192.168.1.100"})

        assert result["name"] == "plug1"
        assert result["ip"] == "192.168.1.100"
        assert result["online"] is True
        assert result["state"] == "on"
        assert result["current_power"] == 50.0
        assert result["today_energy"] == 500.0
        assert result["month_energy"] == 15000.0

    @pytest.mark.asyncio
    async def test_calculates_cost_with_price(self, status_service, plug_service):
        """Calculates electricity cost when price is set"""
        result = await status_service.get_plug_status("plug1", {"ip": "192.168.1.100"})

        # 500 Wh * 0.25 = 0.125 EUR
        assert result["today_cost"] == 0.125
        # 15000 Wh * 0.25 = 3.75 EUR
        assert result["month_cost"] == 3.75
        # 50W * 0.25 = 0.0125 EUR/h
        assert result["current_cost_per_hour"] == 0.0125

    @pytest.mark.asyncio
    async def test_zero_cost_when_price_is_zero(self, status_service, plug_service):
        """Cost is 0 when electricity price is 0"""
        status_service.config.get_electricity_price.return_value = 0.0
        result = await status_service.get_plug_status("plug1", {"ip": "192.168.1.100"})

        assert result["today_cost"] == 0
        assert result["month_cost"] == 0
        assert result["current_cost_per_hour"] == 0

    @pytest.mark.asyncio
    async def test_plug_off_returns_off_state(self, status_service, plug_service):
        """Returns 'off' state when plug is off"""
        plug_service.get_full_status.return_value["on"] = False
        result = await status_service.get_plug_status("plug1", {"ip": "192.168.1.100"})

        assert result["state"] == "off"

    @pytest.mark.asyncio
    async def test_unreachable_plug_returns_offline(self, status_service, plug_service):
        """Returns offline status on exception"""
        plug_service.get_full_status.side_effect = Exception("Connection refused")
        result = await status_service.get_plug_status("plug1", {"ip": "192.168.1.100"})

        assert result["online"] is False
        assert "error" in result
        assert result["name"] == "plug1"


class TestGetServerStatus:
    """Tests for get_server_status"""

    @pytest.mark.asyncio
    async def test_online_server(self, status_service, server_service):
        """Returns correct status for online server"""
        server_service.ping_async.return_value = True
        server_service.resolve_hostname_async.return_value = "192.168.1.50"

        result = await status_service.get_server_status(
            "srv1", {"hostname": "server1.local", "mac": "AA:BB:CC:DD:EE:01", "plug": "plug1"}
        )

        assert result["name"] == "srv1"
        assert result["hostname"] == "server1.local"
        assert result["online"] is True
        assert result["ip"] == "192.168.1.50"
        assert result["mac"] == "AA:BB:CC:DD:EE:01"

    @pytest.mark.asyncio
    async def test_offline_server(self, status_service, server_service):
        """Returns correct status for offline server"""
        server_service.ping_async.return_value = False
        server_service.resolve_hostname_async.return_value = "192.168.1.50"

        result = await status_service.get_server_status(
            "srv1", {"hostname": "server1.local", "mac": "AA:BB:CC:DD:EE:01", "plug": "plug1"}
        )

        assert result["online"] is False

    @pytest.mark.asyncio
    async def test_server_without_plug_has_no_power(self, status_service, server_service):
        """Server without plug has no power data"""
        result = await status_service.get_server_status(
            "srv2", {"hostname": "server2.local", "mac": "AA:BB:CC:DD:EE:02", "plug": None}
        )

        assert "power" not in result

    @pytest.mark.asyncio
    async def test_server_with_plug_includes_power(self, status_service, server_service, plug_service):
        """Server with plug includes power data"""
        result = await status_service.get_server_status(
            "srv1", {"hostname": "server1.local", "mac": "AA:BB:CC:DD:EE:01", "plug": "plug1"}
        )

        assert "power" in result
        assert result["power"]["current"] == 50.0
        assert result["power"]["today_energy"] == 500.0

    @pytest.mark.asyncio
    async def test_server_with_uptime(self, status_service, server_service, config):
        """Server with state includes uptime duration"""
        config.get_server_state.return_value = {
            "online": True,
            "last_change": (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat(),
        }

        result = await status_service.get_server_status(
            "srv1", {"hostname": "server1.local", "mac": "AA:BB:CC:DD:EE:01", "plug": None}
        )

        assert "uptime" in result

    @pytest.mark.asyncio
    async def test_server_with_downtime(self, status_service, server_service, config):
        """Offline server with state includes downtime duration"""
        server_service.ping_async.return_value = False
        config.get_server_state.return_value = {
            "online": False,
            "last_change": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
        }

        result = await status_service.get_server_status(
            "srv1", {"hostname": "server1.local", "mac": "AA:BB:CC:DD:EE:01", "plug": None}
        )

        assert result["online"] is False
        assert "downtime" in result

    @pytest.mark.asyncio
    async def test_plug_fetch_failure_does_not_break_server(self, status_service, server_service, plug_service):
        """Server status still works if plug power fetch fails"""
        plug_service.get_full_status.side_effect = Exception("Plug offline")

        result = await status_service.get_server_status(
            "srv1", {"hostname": "server1.local", "mac": "AA:BB:CC:DD:EE:01", "plug": "plug1"}
        )

        assert result["name"] == "srv1"
        assert result["online"] is True
        assert "power" not in result  # No power data due to failure


class TestGetAllStatus:
    """Tests for get_all_status"""

    @pytest.mark.asyncio
    async def test_returns_all_servers_and_plugs(self, status_service, config):
        """Returns status for all configured devices"""
        result = await status_service.get_all_status()

        assert len(result["servers"]) == 2
        assert len(result["plugs"]) == 2
        assert "summary" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_summary_counts(self, status_service, config):
        """Summary has correct counts"""
        result = await status_service.get_all_status()

        summary = result["summary"]
        assert summary["servers_total"] == 2
        assert summary["plugs_total"] == 2
        assert summary["servers_online"] == 2
        assert summary["plugs_online"] == 2
        assert summary["plugs_on"] == 2
        assert summary["total_power"] == 100.0  # 50W * 2 plugs

    @pytest.mark.asyncio
    async def test_handles_partial_failures(self, status_service, config, plug_service, server_service):
        """Continues when some checks fail"""
        # First plug succeeds, second throws (caught by get_plug_status)
        plug_service.get_full_status.side_effect = [
            {"on": True, "signal_level": 3, "current_power": 50.0,
             "today_runtime": 0, "today_energy": 0, "month_runtime": 0, "month_energy": 0},
            Exception("timeout"),
        ]

        result = await status_service.get_all_status()

        # Both plugs are present — failed one has online=False
        assert len(result["plugs"]) == 2
        ok = next(p for p in result["plugs"] if p["name"] == "plug1")
        fail = next(p for p in result["plugs"] if p["name"] == "plug2")
        assert ok["online"] is True
        assert fail["online"] is False
        assert "error" in fail

    @pytest.mark.asyncio
    async def test_empty_config(self, status_service, config):
        """Handles empty config gracefully"""
        config.list_plugs.return_value = {}
        config.list_servers.return_value = {}

        result = await status_service.get_all_status()

        assert result["summary"]["servers_total"] == 0
        assert result["summary"]["plugs_total"] == 0
        assert result["summary"]["total_power"] == 0
