#!/usr/bin/env python3
"""
Unit tests for Homelab CLI Client
"""

import pytest
import os
from unittest.mock import Mock, patch
from pathlib import Path
import requests

# Import the client
from homelab_client import HomelabClient


class TestStatusOperations:
    """Test status-related operations"""

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.status_manager.requests.get")
    @patch("homelab_client.status_manager.StatusDisplay")
    @patch("builtins.print")
    def test_get_status_success(
        self, mock_print, mock_display_class, mock_get, mock_exists, mock_home
    ):
        """Test getting status successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "servers": [{"name": "server1", "online": True}],
            "plugs": [{"name": "plug1", "is_on": True}],
            "electricity_price": 0.25,
        }
        mock_get.return_value = mock_response

        mock_display = Mock()
        mock_display.format_status_output.return_value = [
            "Status line 1",
            "Status line 2",
        ]
        mock_display_class.return_value = mock_display

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.get_status()

        mock_get.assert_called_once()
        mock_display.format_status_output.assert_called_once()

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.status_manager.requests.get")
    def test_get_status_error(self, mock_get, mock_exists, mock_home):
        """Test get status with error"""
        from homelab_client import ConnectionError

        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_get.side_effect = requests.exceptions.ConnectionError()

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            with pytest.raises(ConnectionError):
                client.get_status()
