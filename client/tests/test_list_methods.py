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
from homelab_client import HomelabClient


class TestListMethodsDetailed:
    """Test list methods with detailed output verification"""

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.get")
    @patch("builtins.print")
    def test_list_plugs_with_multiple_plugs(
        self, mock_print, mock_get, mock_exists, mock_home
    ):
        """Test listing multiple plugs with full output verification"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "plugs": {
                "living-room": {"ip": "192.168.1.10"},
                "bedroom": {"ip": "192.168.1.11"},
                "office": {"ip": "192.168.1.12"},
            }
        }
        mock_get.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.list_plugs()

        # Verify print was called with expected content
        print_calls = [str(call) for call in mock_print.call_args_list]
        combined_output = " ".join(print_calls)
        assert "Configured Plugs" in combined_output
        assert "living-room" in combined_output
        assert "192.168.1.10" in combined_output

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.get")
    @patch("builtins.print")
    def test_list_servers_with_online_status(
        self, mock_print, mock_get, mock_exists, mock_home
    ):
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
                    "online": True,
                },
                "backup-srv": {
                    "hostname": "backup.local",
                    "mac": "AA:BB:CC:DD:EE:FF",
                    "plug": None,
                    "ip": "192.168.1.101",
                    "online": False,
                },
            }
        }
        mock_get.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.list_servers()

        # Verify output contains status indicators
        print_calls = [str(call) for call in mock_print.call_args_list]
        combined_output = " ".join(print_calls)
        assert "Configured Servers" in combined_output
        assert "main-srv" in combined_output
        assert "backup-srv" in combined_output

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.get")
    def test_list_plugs_request_exception(self, mock_get, mock_exists, mock_home):
        """Test list plugs handles request exceptions"""
        from homelab_client import APIError

        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            with pytest.raises(APIError):
                client.list_plugs()

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.get")
    def test_list_servers_request_exception(self, mock_get, mock_exists, mock_home):
        """Test list servers handles request exceptions"""
        from homelab_client import ConnectionError

        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_get.side_effect = requests.exceptions.ConnectionError("Cannot connect")

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            with pytest.raises(ConnectionError):
                client.list_servers()
