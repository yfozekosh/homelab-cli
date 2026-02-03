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

