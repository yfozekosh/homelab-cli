"""Unit tests for PowerControlService"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.power_service import PowerControlService


@pytest.fixture
def plug_service():
    """Mock PlugService"""
    svc = AsyncMock()
    svc.turn_on = AsyncMock()
    svc.turn_off = AsyncMock()
    svc.get_power = AsyncMock(return_value=45.0)
    return svc


@pytest.fixture
def server_service():
    """Mock ServerService"""
    svc = AsyncMock()
    svc.ping_async = AsyncMock(return_value=False)
    svc.send_wol = MagicMock()
    svc.shutdown_async = AsyncMock()
    return svc


@pytest.fixture
def power_service(plug_service, server_service):
    """PowerControlService with mocked dependencies"""
    return PowerControlService(plug_service, server_service)


@pytest.fixture
def server():
    """Sample server config"""
    return {"hostname": "srv1.local", "mac": "AA:BB:CC:DD:EE:01", "plug": "plug1"}


def _fast_forward_time(start=0.0, step=1.0):
    """Create a time.time() mock that advances each call."""
    t = [start]

    def fake_time():
        val = t[0]
        t[0] += step
        return val

    return fake_time


class TestPowerOn:
    """Tests for power_on"""

    @pytest.mark.asyncio
    async def test_success_first_boot(
        self, power_service, plug_service, server_service, server
    ):
        """Server boots on first try after plug turn-on"""
        server_service.ping_async.return_value = True

        result = await power_service.power_on(server, "192.168.1.100")

        assert result["success"] is True
        assert "Server powered on successfully" in result["message"]
        plug_service.turn_on.assert_called_once_with("192.168.1.100")
        assert any("Server responding to ping" in log for log in result["logs"])

    @pytest.mark.asyncio
    async def test_fallback_to_wol(
        self, power_service, plug_service, server_service, server
    ):
        """Sends WOL when server doesn't respond to initial boot"""
        plug_service.get_power.return_value = 3.0  # Low power, triggers WOL

        # _monitor_boot: first call fails, second call succeeds (after WOL)
        monitor_calls = [0]

        async def fake_monitor(*args, **kwargs):
            monitor_calls[0] += 1
            return monitor_calls[0] > 1

        with patch.object(power_service, "_monitor_boot", side_effect=fake_monitor):
            result = await power_service.power_on(server, "192.168.1.100")

        assert result["success"] is True
        assert monitor_calls[0] == 2  # Called twice
        server_service.send_wol.assert_called_once_with("AA:BB:CC:DD:EE:01")

    @pytest.mark.asyncio
    async def test_failure_turns_off_plug(
        self, power_service, plug_service, server_service, server
    ):
        """Turns off plug when server fails to boot even after WOL"""
        plug_service.get_power.return_value = 3.0

        with patch.object(power_service, "_monitor_boot", return_value=False):
            result = await power_service.power_on(server, "192.168.1.100")

        assert result["success"] is False
        assert "Server failed to boot" in result["message"]
        plug_service.turn_off.assert_called_once_with("192.168.1.100")

    @pytest.mark.asyncio
    async def test_progress_callback_called(
        self, power_service, plug_service, server_service, server
    ):
        """Progress callback receives log messages"""
        server_service.ping_async.return_value = True
        progress_messages = []

        def callback(msg):
            progress_messages.append(msg)

        await power_service.power_on(
            server, "192.168.1.100", progress_callback=callback
        )

        assert len(progress_messages) > 0
        assert "Turning on plug..." in progress_messages

    @pytest.mark.asyncio
    async def test_high_power_skips_wol(
        self, power_service, plug_service, server_service, server
    ):
        """Skips WOL fallback when power is high (server already on)"""
        plug_service.get_power.return_value = 60.0

        with patch.object(power_service, "_monitor_boot", return_value=False):
            result = await power_service.power_on(server, "192.168.1.100")

        # High power means server is running; no WOL sent
        server_service.send_wol.assert_not_called()
        # Original code falls through to "online" when power >= 5W even without ping
        assert result["success"] is True
        assert "WOL" not in " ".join(result["logs"])


class TestPowerOff:
    """Tests for power_off"""

    @pytest.mark.asyncio
    async def test_graceful_shutdown(
        self, power_service, plug_service, server_service, server
    ):
        """Sends shutdown command and monitors power drop"""
        # Enough low-power readings to trigger the 10s low-power detection
        plug_service.get_power.return_value = 2.0

        with patch("server.power_service.asyncio.sleep", new_callable=AsyncMock), patch(
            "server.power_service.time.time", side_effect=_fast_forward_time(0, 5)
        ):
            result = await power_service.power_off(server, "192.168.1.100")

        assert result["success"] is True
        server_service.shutdown_async.assert_called_once_with("srv1.local")
        plug_service.turn_off.assert_called_once_with("192.168.1.100")

    @pytest.mark.asyncio
    async def test_shutdown_failure_continues(
        self, power_service, plug_service, server_service, server
    ):
        """Continues monitoring even if shutdown command fails"""
        server_service.shutdown_async.side_effect = Exception("SSH refused")
        plug_service.get_power.return_value = 2.0

        with patch("server.power_service.asyncio.sleep", new_callable=AsyncMock), patch(
            "server.power_service.time.time", side_effect=_fast_forward_time(0, 5)
        ):
            result = await power_service.power_off(server, "192.168.1.100")

        assert result["success"] is True
        assert any("Failed to send shutdown" in log for log in result["logs"])

    @pytest.mark.asyncio
    async def test_timeout_still_turns_off(
        self, power_service, plug_service, server_service, server
    ):
        """Turns off plug even on timeout"""
        plug_service.get_power.return_value = 50.0  # Never drops

        with patch("server.power_service.asyncio.sleep", new_callable=AsyncMock), patch(
            "server.power_service.time.time", side_effect=_fast_forward_time(0, 20)
        ):
            result = await power_service.power_off(server, "192.168.1.100")

        assert any("Timeout" in log for log in result["logs"])
        plug_service.turn_off.assert_called_once_with("192.168.1.100")

    @pytest.mark.asyncio
    async def test_progress_callback_receives_power_readings(
        self, power_service, plug_service, server_service, server
    ):
        """Progress callback receives power readings during shutdown"""
        plug_service.get_power.return_value = 2.0
        messages = []

        def cb(msg):
            messages.append(msg)

        with patch("server.power_service.asyncio.sleep", new_callable=AsyncMock), patch(
            "server.power_service.time.time", side_effect=_fast_forward_time(0, 5)
        ):
            await power_service.power_off(server, "192.168.1.100", progress_callback=cb)

        power_lines = [m for m in messages if "Power:" in m]
        assert len(power_lines) >= 2


class TestMonitorBoot:
    """Tests for _monitor_boot"""

    @pytest.mark.asyncio
    async def test_immediate_ping(self, power_service, server_service):
        """Returns True immediately when server responds"""
        server_service.ping_async.return_value = True
        logs = []

        result = await power_service._monitor_boot(
            {"hostname": "srv1"}, "192.168.1.100", 60, logs.append
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_timeout_returns_false(self, power_service, server_service):
        """Returns False after timeout"""
        server_service.ping_async.return_value = False
        power_service.plug_service.get_power = AsyncMock(return_value=40.0)
        logs = []

        with patch("server.power_service.asyncio.sleep", new_callable=AsyncMock), patch(
            "server.power_service.time.time", side_effect=_fast_forward_time(0, 10)
        ):
            result = await power_service._monitor_boot(
                {"hostname": "srv1"}, "192.168.1.100", 60, logs.append
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_power_read_failure_does_not_crash(
        self, power_service, server_service
    ):
        """Continues monitoring even if power read fails"""
        server_service.ping_async.side_effect = [False, False, True]
        power_service.plug_service.get_power = AsyncMock(
            side_effect=Exception("Plug timeout")
        )
        logs = []

        result = await power_service._monitor_boot(
            {"hostname": "srv1"}, "192.168.1.100", 60, logs.append
        )

        assert result is True
