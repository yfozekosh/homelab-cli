"""Unit tests for PlugService"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import os

from server.plug_service import PlugService


@pytest.fixture
def mock_env():
    """Mock TAPO credentials"""
    with patch.dict(os.environ, {
        'TAPO_USERNAME': 'test@example.com',
        'TAPO_PASSWORD': 'testpassword'
    }):
        yield


@pytest.fixture
def plug_service(mock_env):
    """Create PlugService instance"""
    return PlugService()


class TestPlugServiceInit:
    """Tests for PlugService initialization"""

    def test_init_with_credentials(self, mock_env):
        """Successfully initialize with credentials"""
        service = PlugService()
        assert service.username == 'test@example.com'
        assert service.password == 'testpassword'

    def test_init_without_username_raises(self):
        """Raises ValueError without TAPO_USERNAME"""
        with patch.dict(os.environ, {'TAPO_PASSWORD': 'test'}, clear=True):
            with pytest.raises(ValueError, match="TAPO_USERNAME"):
                PlugService()

    def test_init_without_password_raises(self):
        """Raises ValueError without TAPO_PASSWORD"""
        with patch.dict(os.environ, {'TAPO_USERNAME': 'test'}, clear=True):
            with pytest.raises(ValueError, match="TAPO_PASSWORD"):
                PlugService()


class TestGetClient:
    """Tests for get_client method"""

    @pytest.mark.asyncio
    async def test_get_client_success(self, plug_service):
        """Successfully get client"""
        mock_device = AsyncMock()
        mock_client = MagicMock()
        mock_client.p110 = AsyncMock(return_value=mock_device)
        
        with patch('server.plug_service.ApiClient', return_value=mock_client):
            result = await plug_service.get_client('192.168.1.100')
            assert result == mock_device

    @pytest.mark.asyncio
    async def test_get_client_timeout(self, plug_service):
        """Raises on timeout"""
        mock_client = MagicMock()
        mock_client.p110 = AsyncMock(side_effect=asyncio.TimeoutError())
        
        with patch('server.plug_service.ApiClient', return_value=mock_client):
            with pytest.raises(asyncio.TimeoutError):
                await plug_service.get_client('192.168.1.100', timeout=0.1)


class TestTurnOn:
    """Tests for turn_on method"""

    @pytest.mark.asyncio
    async def test_turn_on_success(self, plug_service):
        """Successfully turn on plug"""
        mock_device = AsyncMock()
        mock_device.on = AsyncMock()
        
        with patch.object(plug_service, 'get_client', return_value=mock_device):
            await plug_service.turn_on('192.168.1.100')
            mock_device.on.assert_called_once()


class TestTurnOff:
    """Tests for turn_off method"""

    @pytest.mark.asyncio
    async def test_turn_off_success(self, plug_service):
        """Successfully turn off plug"""
        mock_device = AsyncMock()
        mock_device.off = AsyncMock()
        
        with patch.object(plug_service, 'get_client', return_value=mock_device):
            await plug_service.turn_off('192.168.1.100')
            mock_device.off.assert_called_once()


class TestGetPower:
    """Tests for get_power method"""

    @pytest.mark.asyncio
    async def test_get_power_success(self, plug_service):
        """Successfully get power"""
        mock_energy = MagicMock()
        mock_energy.current_power = 42.5
        mock_device = AsyncMock()
        mock_device.get_current_power = AsyncMock(return_value=mock_energy)
        
        with patch.object(plug_service, 'get_client', return_value=mock_device):
            result = await plug_service.get_power('192.168.1.100')
            assert result == 42.5


class TestGetStatus:
    """Tests for get_status method"""

    @pytest.mark.asyncio
    async def test_get_status_success(self, plug_service):
        """Successfully get status"""
        mock_info = MagicMock()
        mock_info.device_on = True
        mock_info.signal_level = 3
        mock_device = AsyncMock()
        mock_device.get_device_info = AsyncMock(return_value=mock_info)
        
        with patch.object(plug_service, 'get_client', return_value=mock_device):
            result = await plug_service.get_status('192.168.1.100')
            assert result == {'on': True, 'signal_level': 3}

    @pytest.mark.asyncio
    async def test_get_status_failure_returns_defaults(self, plug_service):
        """Returns default values on failure"""
        with patch.object(plug_service, 'get_client', side_effect=Exception('Connection failed')):
            result = await plug_service.get_status('192.168.1.100')
            assert result == {'on': False, 'signal_level': 0}


class TestGetEnergyUsage:
    """Tests for get_energy_usage method"""

    @pytest.mark.asyncio
    async def test_get_energy_usage_success(self, plug_service):
        """Successfully get energy usage"""
        mock_current = MagicMock()
        mock_current.current_power = 50.0
        
        mock_energy = MagicMock()
        mock_energy.today_runtime = 120
        mock_energy.today_energy = 500
        mock_energy.month_runtime = 3600
        mock_energy.month_energy = 15000
        
        mock_device = AsyncMock()
        mock_device.get_current_power = AsyncMock(return_value=mock_current)
        mock_device.get_energy_usage = AsyncMock(return_value=mock_energy)
        
        with patch.object(plug_service, 'get_client', return_value=mock_device):
            result = await plug_service.get_energy_usage('192.168.1.100')
            assert result == {
                'current_power': 50.0,
                'today_runtime': 120,
                'today_energy': 500,
                'month_runtime': 3600,
                'month_energy': 15000,
            }

    @pytest.mark.asyncio
    async def test_get_energy_usage_failure_returns_zeros(self, plug_service):
        """Returns zeros on failure"""
        with patch.object(plug_service, 'get_client', side_effect=Exception('Error')):
            result = await plug_service.get_energy_usage('192.168.1.100')
            assert result == {
                'current_power': 0,
                'today_runtime': 0,
                'today_energy': 0,
                'month_runtime': 0,
                'month_energy': 0,
            }


class TestGetFullStatus:
    """Tests for get_full_status method"""

    @pytest.mark.asyncio
    async def test_get_full_status_success(self, plug_service):
        """Successfully get full status"""
        mock_info = MagicMock()
        mock_info.device_on = True
        mock_info.signal_level = 3
        mock_device = AsyncMock()
        mock_device.get_device_info = AsyncMock(return_value=mock_info)
        
        energy_data = {
            'current_power': 50.0,
            'today_runtime': 120,
            'today_energy': 500,
            'month_runtime': 3600,
            'month_energy': 15000,
        }
        
        with patch.object(plug_service, 'get_client', return_value=mock_device):
            with patch.object(plug_service, 'get_energy_usage', return_value=energy_data):
                result = await plug_service.get_full_status('192.168.1.100')
                assert result['on'] is True
                assert result['signal_level'] == 3
                assert result['current_power'] == 50.0

    @pytest.mark.asyncio
    async def test_get_full_status_failure_returns_offline(self, plug_service):
        """Returns offline status on failure"""
        with patch.object(plug_service, 'get_client', side_effect=Exception('Error')):
            result = await plug_service.get_full_status('192.168.1.100')
            assert result['on'] is False
            assert result['signal_level'] == 0
            assert result['current_power'] == 0
