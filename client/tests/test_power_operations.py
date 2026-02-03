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


class TestPowerOperations:
    """Test power on/off operations"""

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.power_manager.requests.post")
    @patch("builtins.print")
    def test_power_on_success(self, mock_print, mock_post, mock_exists, mock_home):
        """Test power on successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")

        # Mock SSE streaming response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b"event: log",
            b'data: {"message": "Turning on plug..."}',
            b"",
            b"event: log",
            b'data: {"message": "Server is online!"}',
            b"",
            b'data: {"success": true, "message": "Powered on"}',
        ]
        mock_post.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.power_on("test-server")

        mock_post.assert_called_once()
        assert any(
            "powered on successfully" in str(call) for call in mock_print.call_args_list
        )

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.power_manager.requests.post")
    @patch("builtins.print")
    def test_power_on_failure(self, mock_print, mock_post, mock_exists, mock_home):
        """Test power on failure"""
        from homelab_client import APIError

        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")

        # Mock SSE streaming response with failure
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b"event: log",
            b'data: {"message": "Turning on plug..."}',
            b"",
            b'data: {"success": false, "message": "Server not configured"}',
        ]
        mock_post.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            with pytest.raises(APIError):
                client.power_on("test-server")

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.power_manager.requests.post")
    @patch("builtins.print")
    def test_power_off_success(self, mock_print, mock_post, mock_exists, mock_home):
        """Test power off successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")

        # Mock SSE streaming response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b"event: log",
            b'data: {"message": "Sending shutdown..."}',
            b"",
            b'data: {"success": true, "message": "Powered off"}',
        ]
        mock_post.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.power_off("test-server")

        mock_post.assert_called_once()
        assert any(
            "powered off successfully" in str(call)
            for call in mock_print.call_args_list
        )
