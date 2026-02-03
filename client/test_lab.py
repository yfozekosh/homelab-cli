#!/usr/bin/env python3
"""
Unit tests for Homelab CLI Client
"""
import pytest
import json
import sys
import os
import threading
from unittest.mock import Mock, patch, mock_open, MagicMock
from pathlib import Path
import requests

# Import the client
from lab import HomelabClient


class TestHomelabClientInit:
    """Test HomelabClient initialization"""
    
    @patch('lab.Path.home')
    @patch('builtins.open', new_callable=mock_open, read_data='{"server_url": "http://test.local", "api_key": "test-key"}')
    @patch('lab.Path.exists')
    def test_init_with_config_file(self, mock_exists, mock_file, mock_home):
        """Test initialization with config file"""
        mock_exists.return_value = True
        mock_home.return_value = Path("/home/test")
        
        client = HomelabClient()
        
        assert client.server_url == "http://test.local"
        assert client.api_key == "test-key"
        assert client.headers == {"X-API-Key": "test-key"}
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    def test_init_with_parameters(self, mock_exists, mock_home):
        """Test initialization with explicit parameters"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        client = HomelabClient(server_url="http://custom.local", api_key="custom-key")
        
        assert client.server_url == "http://custom.local"
        assert client.api_key == "custom-key"
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://env.local', 'HOMELAB_API_KEY': 'env-key'})
    def test_init_with_environment_variables(self, mock_exists, mock_home):
        """Test initialization with environment variables"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        client = HomelabClient()
        
        assert client.server_url == "http://env.local"
        assert client.api_key == "env-key"
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    def test_init_missing_server_url(self, mock_exists, mock_home):
        """Test initialization fails without server URL"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with pytest.raises(SystemExit) as exc_info:
            HomelabClient()
        
        assert exc_info.value.code == 1
    
    @patch('lab.Path.home')
    @patch('builtins.open', new_callable=mock_open, read_data='{"server_url": "http://test.local"}')
    @patch('lab.Path.exists')
    def test_init_missing_api_key(self, mock_exists, mock_file, mock_home):
        """Test initialization fails without API key"""
        mock_exists.return_value = True
        mock_home.return_value = Path("/home/test")
        
        with pytest.raises(SystemExit) as exc_info:
            HomelabClient()
        
        assert exc_info.value.code == 1


class TestConfigMethods:
    """Test configuration loading and saving"""
    
    @patch('lab.Path.home')
    @patch('builtins.open', new_callable=mock_open)
    @patch('lab.Path.exists')
    def test_load_config_success(self, mock_exists, mock_file, mock_home):
        """Test successful config loading"""
        mock_exists.return_value = True
        mock_home.return_value = Path("/home/test")
        config_data = '{"server_url": "http://test.local", "api_key": "test-key"}'
        mock_file.return_value.read.return_value = config_data
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://env.local', 'HOMELAB_API_KEY': 'env-key'}):
            client = HomelabClient()
            config = client._load_config()
        
        assert "server_url" in config
        assert "api_key" in config
    
    @patch('lab.Path.home')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('lab.Path.exists')
    def test_load_config_invalid_json(self, mock_exists, mock_file, mock_home):
        """Test config loading with invalid JSON"""
        mock_exists.return_value = True
        mock_home.return_value = Path("/home/test")
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://env.local', 'HOMELAB_API_KEY': 'env-key'}):
            client = HomelabClient()
            config = client._load_config()
        
        assert config == {}
    
    @patch('lab.Path.home')
    @patch('builtins.open', new_callable=mock_open)
    @patch('lab.Path.exists')
    @patch('lab.Path.mkdir')
    def test_save_config(self, mock_mkdir, mock_exists, mock_file, mock_home):
        """Test config saving"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://env.local', 'HOMELAB_API_KEY': 'env-key'}):
            client = HomelabClient()
            client._save_config({"server_url": "http://new.local", "api_key": "new-key"})
        
        mock_mkdir.assert_called_once()
        mock_file.assert_called()


class TestHealthCheck:
    """Test health check functionality"""
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.get')
    def test_health_check_success(self, mock_get, mock_exists, mock_home):
        """Test successful health check"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            result = client.health_check()
        
        assert result is True
        mock_get.assert_called_once_with("http://test.local/health", timeout=5)
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.get')
    def test_health_check_failure(self, mock_get, mock_exists, mock_home):
        """Test failed health check"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            result = client.health_check()
        
        assert result is False


class TestPlugOperations:
    """Test plug-related operations"""
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.get')
    @patch('builtins.print')
    def test_list_plugs_success(self, mock_print, mock_get, mock_exists, mock_home):
        """Test listing plugs successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "plugs": {
                "plug1": {"ip": "192.168.1.10"},
                "plug2": {"ip": "192.168.1.11"}
            }
        }
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.list_plugs()
        
        mock_get.assert_called_once()
        assert mock_print.call_count > 0
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.get')
    @patch('builtins.print')
    def test_list_plugs_empty(self, mock_print, mock_get, mock_exists, mock_home):
        """Test listing plugs when none configured"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.json.return_value = {"plugs": {}}
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.list_plugs()
        
        mock_print.assert_any_call("No plugs configured")
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.post')
    @patch('builtins.print')
    def test_add_plug_success(self, mock_print, mock_post, mock_exists, mock_home):
        """Test adding plug successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.add_plug("test-plug", "192.168.1.10")
        
        mock_post.assert_called_once()
        mock_print.assert_called_with("✓ Plug 'test-plug' added successfully")
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.put')
    @patch('builtins.print')
    def test_edit_plug_success(self, mock_print, mock_put, mock_exists, mock_home):
        """Test editing plug successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.edit_plug("test-plug", "192.168.1.20")
        
        mock_put.assert_called_once()
        args = mock_put.call_args
        assert args[1]['json'] == {"name": "test-plug", "ip": "192.168.1.20"}
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.delete')
    @patch('builtins.print')
    def test_remove_plug_success(self, mock_print, mock_delete, mock_exists, mock_home):
        """Test removing plug successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.remove_plug("test-plug")
        
        mock_delete.assert_called_once()
        mock_print.assert_called_with("✓ Plug 'test-plug' removed successfully")
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.post')
    def test_add_plug_error(self, mock_post, mock_exists, mock_home):
        """Test add plug with error"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            with pytest.raises(SystemExit):
                client.add_plug("test-plug", "192.168.1.10")


class TestServerOperations:
    """Test server-related operations"""
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.get')
    @patch('builtins.print')
    def test_list_servers_success(self, mock_print, mock_get, mock_exists, mock_home):
        """Test listing servers successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.json.return_value = {
            "servers": {
                "server1": {
                    "hostname": "host1.local",
                    "mac": "00:11:22:33:44:55",
                    "plug": "plug1",
                    "ip": "192.168.1.100",
                    "online": True
                }
            }
        }
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.list_servers()
        
        mock_get.assert_called_once()
        assert mock_print.call_count > 0
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.post')
    @patch('builtins.print')
    def test_add_server_success(self, mock_print, mock_post, mock_exists, mock_home):
        """Test adding server successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.add_server("test-server", "host.local", mac="00:11:22:33:44:55", plug="plug1")
        
        mock_post.assert_called_once()
        args = mock_post.call_args
        assert args[1]['json']['name'] == "test-server"
        assert args[1]['json']['hostname'] == "host.local"
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.post')
    @patch('builtins.print')
    def test_add_server_minimal(self, mock_print, mock_post, mock_exists, mock_home):
        """Test adding server with minimal parameters"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.add_server("test-server", "host.local")
        
        args = mock_post.call_args
        assert args[1]['json']['mac'] is None
        assert args[1]['json']['plug'] is None
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.put')
    @patch('builtins.print')
    def test_edit_server_success(self, mock_print, mock_put, mock_exists, mock_home):
        """Test editing server successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.edit_server("test-server", hostname="newhost.local", mac="AA:BB:CC:DD:EE:FF")
        
        mock_put.assert_called_once()
        args = mock_put.call_args
        assert args[1]['json']['hostname'] == "newhost.local"
        assert args[1]['json']['mac'] == "AA:BB:CC:DD:EE:FF"
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.delete')
    @patch('builtins.print')
    def test_remove_server_success(self, mock_print, mock_delete, mock_exists, mock_home):
        """Test removing server successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.remove_server("test-server")
        
        mock_delete.assert_called_once()


class TestPowerOperations:
    """Test power on/off operations"""
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.post')
    @patch('builtins.print')
    def test_power_on_success(self, mock_print, mock_post, mock_exists, mock_home):
        """Test power on successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "message": "Powered on",
            "logs": ["Log 1", "Log 2"]
        }
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.power_on("test-server")
        
        mock_post.assert_called_once()
        assert any("powered on successfully" in str(call) for call in mock_print.call_args_list)
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.post')
    @patch('builtins.print')
    def test_power_on_failure(self, mock_print, mock_post, mock_exists, mock_home):
        """Test power on failure"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": False,
            "message": "Server not configured"
        }
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            with pytest.raises(SystemExit):
                client.power_on("test-server")
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.post')
    @patch('builtins.print')
    def test_power_off_success(self, mock_print, mock_post, mock_exists, mock_home):
        """Test power off successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "message": "Powered off"
        }
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.power_off("test-server")
        
        mock_post.assert_called_once()
        assert any("powered off successfully" in str(call) for call in mock_print.call_args_list)


class TestConfigCommands:
    """Test configuration commands"""
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('lab.Path.mkdir')
    @patch('builtins.print')
    def test_set_server_url(self, mock_print, mock_mkdir, mock_file, mock_exists, mock_home):
        """Test setting server URL"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.set_server_url("http://newserver.local")
        
        mock_print.assert_called_with("✓ Server URL set to: http://newserver.local")
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('lab.Path.mkdir')
    @patch('builtins.print')
    def test_set_api_key(self, mock_print, mock_mkdir, mock_file, mock_exists, mock_home):
        """Test setting API key"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.set_api_key("new-api-key")
        
        mock_print.assert_called_with("✓ API key saved")


class TestElectricityPrice:
    """Test electricity price operations"""
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.post')
    @patch('builtins.print')
    def test_set_electricity_price_success(self, mock_print, mock_post, mock_exists, mock_home):
        """Test setting electricity price"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.set_electricity_price(0.25)
        
        args = mock_post.call_args
        assert args[1]['json']['price'] == 0.25
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.get')
    @patch('builtins.print')
    def test_get_electricity_price_success(self, mock_print, mock_get, mock_exists, mock_home):
        """Test getting electricity price"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"price": 0.25}
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.get_electricity_price()
        
        assert any("0.25" in str(call) for call in mock_print.call_args_list)
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.get')
    @patch('builtins.print')
    def test_get_electricity_price_not_set(self, mock_print, mock_get, mock_exists, mock_home):
        """Test getting electricity price when not set"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"price": 0}
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.get_electricity_price()
        
        assert any("No electricity price set" in str(call) for call in mock_print.call_args_list)


class TestStatusOperations:
    """Test status-related operations"""
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.get')
    @patch('lab.StatusDisplay')
    @patch('builtins.print')
    def test_get_status_success(self, mock_print, mock_display_class, mock_get, mock_exists, mock_home):
        """Test getting status successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "servers": [{"name": "server1", "online": True}],
            "plugs": [{"name": "plug1", "is_on": True}],
            "electricity_price": 0.25
        }
        mock_get.return_value = mock_response
        
        mock_display = Mock()
        mock_display.format_status_output.return_value = ["Status line 1", "Status line 2"]
        mock_display_class.return_value = mock_display
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.get_status()
        
        mock_get.assert_called_once()
        mock_display.format_status_output.assert_called_once()
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.get')
    def test_get_status_error(self, mock_get, mock_exists, mock_home):
        """Test get status with error"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            with pytest.raises(SystemExit):
                client.get_status()


class TestWaitForInput:
    """Test keyboard input waiting functionality"""
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.os.name', 'posix')
    @patch('select.select')
    @patch('sys.stdin')
    @patch('time.sleep')
    def test_wait_for_input_q_pressed(self, mock_sleep, mock_stdin, mock_select, mock_exists, mock_home):
        """Test wait for input when 'q' is pressed"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_select.return_value = ([mock_stdin], [], [])
        mock_stdin.read.return_value = 'q'
        
        stop_event = threading.Event()
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            result = client._wait_for_input(0.1, stop_event)
        
        # Should return False when 'q' is pressed
        assert result is False
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.os.name', 'posix')
    @patch('select.select')
    @patch('sys.stdin')
    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_input_timeout(self, mock_time, mock_sleep, mock_stdin, mock_select, mock_exists, mock_home):
        """Test wait for input timeout"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        # Simulate time progressing beyond interval
        mock_time.side_effect = [0, 0.05, 0.2]  # Start, during loop, after interval
        mock_select.return_value = ([], [], [])
        
        stop_event = threading.Event()
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            result = client._wait_for_input(0.1, stop_event)
        
        # Should return True when timeout is reached
        assert result is True
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.os.name', 'posix')
    @patch('select.select')
    @patch('sys.stdin')
    @patch('time.sleep')
    def test_wait_for_input_stop_event(self, mock_sleep, mock_stdin, mock_select, mock_exists, mock_home):
        """Test wait for input with stop event"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_select.return_value = ([], [], [])
        
        stop_event = threading.Event()
        stop_event.set()  # Set event immediately
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            result = client._wait_for_input(5.0, stop_event)
        
        # Should return False when stop_event is set
        assert result is False
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    def test_wait_for_input_method_exists(self, mock_exists, mock_home):
        """Test wait for input method exists"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            assert hasattr(client, '_wait_for_input')


class TestListMethodsDetailed:
    """Test list methods with detailed output verification"""
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.get')
    @patch('builtins.print')
    def test_list_plugs_with_multiple_plugs(self, mock_print, mock_get, mock_exists, mock_home):
        """Test listing multiple plugs with full output verification"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "plugs": {
                "living-room": {"ip": "192.168.1.10"},
                "bedroom": {"ip": "192.168.1.11"},
                "office": {"ip": "192.168.1.12"}
            }
        }
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.list_plugs()
        
        # Verify print was called with expected content
        print_calls = [str(call) for call in mock_print.call_args_list]
        combined_output = ' '.join(print_calls)
        assert 'Configured Plugs' in combined_output
        assert 'living-room' in combined_output
        assert '192.168.1.10' in combined_output
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.get')
    @patch('builtins.print')
    def test_list_servers_with_online_status(self, mock_print, mock_get, mock_exists, mock_home):
        """Test listing servers with online/offline status"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "servers": {
                "main-srv": {
                    "hostname": "main.local",
                    "mac": "00:11:22:33:44:55",
                    "plug": "plug1",
                    "ip": "192.168.1.100",
                    "online": True
                },
                "backup-srv": {
                    "hostname": "backup.local",
                    "mac": "AA:BB:CC:DD:EE:FF",
                    "plug": None,
                    "ip": "192.168.1.101",
                    "online": False
                }
            }
        }
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.list_servers()
        
        # Verify output contains status indicators
        print_calls = [str(call) for call in mock_print.call_args_list]
        combined_output = ' '.join(print_calls)
        assert 'Configured Servers' in combined_output
        assert 'main-srv' in combined_output
        assert 'backup-srv' in combined_output
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.get')
    def test_list_plugs_request_exception(self, mock_get, mock_exists, mock_home):
        """Test list plugs handles request exceptions"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            with pytest.raises(SystemExit) as exc_info:
                client.list_plugs()
            assert exc_info.value.code == 1
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.get')
    def test_list_servers_request_exception(self, mock_get, mock_exists, mock_home):
        """Test list servers handles request exceptions"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_get.side_effect = requests.exceptions.ConnectionError("Cannot connect")
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            with pytest.raises(SystemExit) as exc_info:
                client.list_servers()
            assert exc_info.value.code == 1


class TestGetStatusAdvanced:
    """Test get_status with various scenarios"""
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.get')
    @patch('lab.StatusDisplay')
    @patch('builtins.print')
    @patch('lab.os.name', 'posix')
    @patch('termios.tcgetattr')
    @patch('termios.tcsetattr')
    @patch('tty.setcbreak')
    def test_get_status_with_follow_keyboard_interrupt(self, mock_setcbreak, mock_tcsetattr, 
                                                        mock_tcgetattr, mock_print, mock_display_class,
                                                        mock_get, mock_exists, mock_home):
        """Test get_status with follow mode interrupted by Ctrl+C"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_tcgetattr.return_value = "settings"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "summary": {"servers_online": 0, "servers_total": 0, "plugs_on": 0, 
                       "plugs_total": 0, "plugs_online": 0, "total_power": 0},
            "servers": [],
            "plugs": []
        }
        mock_get.return_value = mock_response
        
        mock_display = Mock()
        mock_display.format_status_output.return_value = ["Test output"]
        mock_display_class.return_value = mock_display
        
        # Simulate KeyboardInterrupt on first call
        mock_get.side_effect = KeyboardInterrupt()
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.get_status(follow_interval=1.0)
        
        # Should print stop message
        print_calls = [str(call) for call in mock_print.call_args_list]
        combined = ' '.join(print_calls)
        assert 'stopped' in combined.lower()
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.get')
    @patch('lab.StatusDisplay')
    @patch('builtins.print')
    @patch('time.strftime')
    def test_get_status_one_time_mode(self, mock_strftime, mock_print, mock_display_class,
                                      mock_get, mock_exists, mock_home):
        """Test get_status in one-time (non-follow) mode"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_strftime.return_value = "2024-01-01 12:00:00"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "summary": {"servers_online": 1, "servers_total": 1, "plugs_on": 1,
                       "plugs_total": 1, "plugs_online": 1, "total_power": 75.0},
            "servers": [{"name": "test-srv", "online": True}],
            "plugs": [{"name": "test-plug", "is_on": True}]
        }
        mock_get.return_value = mock_response
        
        mock_display = Mock()
        mock_display.format_status_output.return_value = ["Status line 1", "Status line 2"]
        mock_display_class.return_value = mock_display
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.get_status(follow_interval=None)
        
        # Verify display was called once with correct parameters
        mock_display.format_status_output.assert_called_once_with(
            mock_response.json.return_value,
            "2024-01-01 12:00:00",
            None
        )
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.get')
    def test_get_status_request_error(self, mock_get, mock_exists, mock_home):
        """Test get_status handles request errors"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            with pytest.raises(SystemExit) as exc_info:
                client.get_status()
            assert exc_info.value.code == 1


class TestPowerOperationsDetailed:
    """Test power operations with more detail"""
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.post')
    @patch('builtins.print')
    def test_power_on_with_logs(self, mock_print, mock_post, mock_exists, mock_home):
        """Test power on displays logs"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "message": "Server powered on",
            "logs": [
                "Turning on plug...",
                "Plug on",
                "Sending WOL packet...",
                "WOL sent",
                "Server is online"
            ]
        }
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.power_on("test-server")
        
        # Verify logs are printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        combined = ' '.join(print_calls)
        assert 'Logs' in combined or 'online' in combined.lower()
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.post')
    @patch('builtins.print')
    def test_power_off_with_logs(self, mock_print, mock_post, mock_exists, mock_home):
        """Test power off displays logs"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "message": "Server powered off",
            "logs": [
                "Sending shutdown command...",
                "Server shut down",
                "Turning off plug..."
            ]
        }
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.power_off("test-server")
        
        # Verify success message
        print_calls = [str(call) for call in mock_print.call_args_list]
        combined = ' '.join(print_calls)
        assert 'powered off' in combined.lower()
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.post')
    @patch('builtins.print')
    def test_power_off_warning_message(self, mock_print, mock_post, mock_exists, mock_home):
        """Test power off displays warning messages"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": False,
            "message": "Server already offline"
        }
        mock_post.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.power_off("test-server")
        
        # Should print warning emoji
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert len(print_calls) > 0
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.post')
    def test_power_operations_network_error(self, mock_post, mock_exists, mock_home):
        """Test power operations handle network errors"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_post.side_effect = requests.exceptions.ConnectionError("Network down")
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            with pytest.raises(SystemExit):
                client.power_on("test-server")


class TestEditOperations:
    """Test edit operations with various parameter combinations"""
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.put')
    @patch('builtins.print')
    def test_edit_server_hostname_only(self, mock_print, mock_put, mock_exists, mock_home):
        """Test editing only hostname"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.edit_server("test-server", hostname="newhost.local")
        
        # Verify only hostname is in request
        args = mock_put.call_args
        assert 'hostname' in args[1]['json']
        assert 'mac' not in args[1]['json']
        assert 'plug' not in args[1]['json']
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.put')
    @patch('builtins.print')
    def test_edit_server_all_fields(self, mock_print, mock_put, mock_exists, mock_home):
        """Test editing all server fields"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.edit_server("test-server", hostname="new.local", mac="AA:BB:CC:DD:EE:FF", plug="new-plug")
        
        # Verify all fields are in request
        args = mock_put.call_args
        assert args[1]['json']['hostname'] == "new.local"
        assert args[1]['json']['mac'] == "AA:BB:CC:DD:EE:FF"
        assert args[1]['json']['plug'] == "new-plug"
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.requests.put')
    def test_edit_operations_http_error(self, mock_put, mock_exists, mock_home):
        """Test edit operations handle HTTP errors"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_put.return_value = mock_response
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            with pytest.raises(SystemExit):
                client.edit_server("nonexistent", hostname="test.local")


class TestMainFunction:
    """Test main() CLI entry point"""
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'plug', 'list'])
    def test_main_plug_list(self, mock_exists, mock_home):
        """Test main with plug list command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'list_plugs') as mock_list:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_list.assert_called_once()
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'server', 'list'])
    def test_main_server_list(self, mock_exists, mock_home):
        """Test main with server list command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'list_servers') as mock_list:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_list.assert_called_once()
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'on', 'test-server'])
    def test_main_power_on(self, mock_exists, mock_home):
        """Test main with power on command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'power_on') as mock_power_on:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_power_on.assert_called_once_with('test-server')
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'off', 'test-server'])
    def test_main_power_off(self, mock_exists, mock_home):
        """Test main with power off command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'power_off') as mock_power_off:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_power_off.assert_called_once_with('test-server')
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'status'])
    def test_main_status(self, mock_exists, mock_home):
        """Test main with status command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'get_status') as mock_status:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_status.assert_called_once_with(follow_interval=None)
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'status', '-f'])
    def test_main_status_follow_default(self, mock_exists, mock_home):
        """Test main with status follow (default interval)"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'get_status') as mock_status:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_status.assert_called_once_with(follow_interval=5.0)
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'status', '-f', '2.5'])
    def test_main_status_follow_custom_interval(self, mock_exists, mock_home):
        """Test main with status follow custom interval"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'get_status') as mock_status:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_status.assert_called_once_with(follow_interval=2.5)
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'set', 'price', '0.25'])
    def test_main_set_price(self, mock_exists, mock_home):
        """Test main with set price command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'set_electricity_price') as mock_set:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_set.assert_called_once_with(0.25)
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'get', 'price'])
    def test_main_get_price(self, mock_exists, mock_home):
        """Test main with get price command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'get_electricity_price') as mock_get:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_get.assert_called_once()
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'plug', 'add', 'new-plug', '192.168.1.50'])
    def test_main_plug_add(self, mock_exists, mock_home):
        """Test main with plug add command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'add_plug') as mock_add:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_add.assert_called_once_with('new-plug', '192.168.1.50')
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'server', 'add', 'new-server', 'host.local', '00:11:22:33:44:55', 'plug1'])
    def test_main_server_add_full(self, mock_exists, mock_home):
        """Test main with server add command (all params)"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'add_server') as mock_add:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_add.assert_called_once_with('new-server', 'host.local', '00:11:22:33:44:55', 'plug1')
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'server', 'edit', 'test-server', '--hostname', 'newhost.local'])
    def test_main_server_edit(self, mock_exists, mock_home):
        """Test main with server edit command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'edit_server') as mock_edit:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        # Check it was called with name and hostname
        assert mock_edit.called
        args, kwargs = mock_edit.call_args
        assert args[0] == 'test-server'
        assert 'hostname' in kwargs or (len(args) > 1 and args[1] == 'newhost.local')
    
    @patch('sys.argv', ['lab'])
    def test_main_no_command(self):
        """Test main with no command shows help"""
        from lab import main
        # Should return without error
        result = main()
        # Function returns None on help
        assert result is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
