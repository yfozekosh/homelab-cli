#!/usr/bin/env python3
"""
Unit tests for Homelab CLI Client
"""

import os
from unittest.mock import patch, mock_open
from pathlib import Path

# Import the client
from homelab_client import HomelabClient


class TestConfigCommands:
    """Test configuration commands"""

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("homelab_client.config.Path.mkdir")
    @patch("builtins.print")
    def test_set_server_url(
        self, mock_print, mock_mkdir, mock_file, mock_exists, mock_home
    ):
        """Test setting server URL"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.set_server_url("http://newserver.local")

        mock_print.assert_called_with("✓ Server URL set to: http://newserver.local")

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("homelab_client.config.Path.mkdir")
    @patch("builtins.print")
    def test_set_api_key(
        self, mock_print, mock_mkdir, mock_file, mock_exists, mock_home
    ):
        """Test setting API key"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.set_api_key("new-api-key")

        mock_print.assert_called_with("✓ API key saved")
