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


class TestEditOperations:
    """Test edit operations with various parameter combinations"""

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.put")
    @patch("builtins.print")
    def test_edit_server_hostname_only(
        self, mock_print, mock_put, mock_exists, mock_home
    ):
        """Test editing only hostname"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.edit_server("test-server", hostname="newhost.local")

        # Verify only hostname is in request
        args = mock_put.call_args
        assert "hostname" in args[1]["json"]
        assert "mac" not in args[1]["json"]
        assert "plug" not in args[1]["json"]

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.put")
    @patch("builtins.print")
    def test_edit_server_all_fields(self, mock_print, mock_put, mock_exists, mock_home):
        """Test editing all server fields"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.edit_server(
                "test-server",
                hostname="new.local",
                mac="AA:BB:CC:DD:EE:FF",
                plug="new-plug",
            )

        # Verify all fields are in request
        args = mock_put.call_args
        assert args[1]["json"]["hostname"] == "new.local"
        assert args[1]["json"]["mac"] == "AA:BB:CC:DD:EE:FF"
        assert args[1]["json"]["plug"] == "new-plug"

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.put")
    def test_edit_operations_http_error(self, mock_put, mock_exists, mock_home):
        """Test edit operations handle HTTP errors"""
        from homelab_client import APIError

        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_put.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            with pytest.raises(APIError):
                client.edit_server("nonexistent", hostname="test.local")
