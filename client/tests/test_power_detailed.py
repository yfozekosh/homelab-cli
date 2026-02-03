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


class TestPowerOperationsDetailed:
    """Test power operations with more detail"""

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.power_manager.requests.post")
    @patch("builtins.print")
    def test_power_on_with_logs(self, mock_print, mock_post, mock_exists, mock_home):
        """Test power on displays logs"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")

        # Mock SSE streaming response with logs
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b"event: log",
            b'data: {"message": "Turning on plug..."}',
            b"",
            b"event: log",
            b'data: {"message": "Plug on"}',
            b"",
            b"event: log",
            b'data: {"message": "Sending WOL packet..."}',
            b"",
            b"event: log",
            b'data: {"message": "Server is online"}',
            b"",
            b'data: {"success": true, "message": "Server powered on"}',
        ]
        mock_post.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.power_on("test-server")

        # Verify logs are printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        combined = " ".join(print_calls)
        assert "Turning on plug" in combined or "online" in combined.lower()

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.power_manager.requests.post")
    @patch("builtins.print")
    def test_power_off_with_logs(self, mock_print, mock_post, mock_exists, mock_home):
        """Test power off displays logs"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")

        # Mock SSE streaming response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b"event: log",
            b'data: {"message": "Sending shutdown command..."}',
            b"",
            b"event: log",
            b'data: {"message": "Server shut down"}',
            b"",
            b"event: log",
            b'data: {"message": "Turning off plug..."}',
            b"",
            b'data: {"success": true, "message": "Server powered off"}',
        ]
        mock_post.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.power_off("test-server")

        # Verify success message
        print_calls = [str(call) for call in mock_print.call_args_list]
        combined = " ".join(print_calls)
        assert "powered off" in combined.lower()

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.power_manager.requests.post")
    @patch("builtins.print")
    def test_power_off_warning_message(
        self, mock_print, mock_post, mock_exists, mock_home
    ):
        """Test power off displays warning messages"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")

        # Mock SSE streaming response with warning
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'data: {"success": false, "message": "Server already offline"}',
        ]
        mock_post.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.power_off("test-server")

        # Should print warning emoji
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert len(print_calls) > 0

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.power_manager.requests.post")
    def test_power_operations_network_error(self, mock_post, mock_exists, mock_home):
        """Test power operations handle network errors"""
        from homelab_client import ConnectionError

        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_post.side_effect = requests.exceptions.ConnectionError("Network down")

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            with pytest.raises(ConnectionError):
                client.power_on("test-server")
