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
    @patch("homelab_client.api_client.requests.post")
    @patch("builtins.print")
    def test_power_on_success(self, mock_print, mock_post, mock_exists, mock_home):
        """Test power on successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "message": "Powered on",
            "logs": ["Log 1", "Log 2"],
        }
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
    @patch("homelab_client.api_client.requests.post")
    @patch("builtins.print")
    def test_power_on_failure(self, mock_print, mock_post, mock_exists, mock_home):
        """Test power on failure"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": False,
            "message": "Server not configured",
        }
        mock_post.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            with pytest.raises(SystemExit):
                client.power_on("test-server")

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.post")
    @patch("builtins.print")
    def test_power_off_success(self, mock_print, mock_post, mock_exists, mock_home):
        """Test power off successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "message": "Powered off"}
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
