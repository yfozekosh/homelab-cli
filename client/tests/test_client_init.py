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
from homelab_client import HomelabClient, ConfigurationError


class TestHomelabClientInit:
    """Test HomelabClient initialization"""

    @patch("homelab_client.config.Path.home")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"server_url": "http://test.local", "api_key": "test-key"}',
    )
    @patch("homelab_client.config.Path.exists")
    def test_init_with_config_file(self, mock_exists, mock_file, mock_home):
        """Test initialization with config file"""
        mock_exists.return_value = True
        mock_home.return_value = Path("/home/test")

        client = HomelabClient()

        assert client.server_url == "http://test.local"
        assert client.api_key == "test-key"
        assert client.headers == {"X-API-Key": "test-key"}

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    def test_init_with_parameters(self, mock_exists, mock_home):
        """Test initialization with explicit parameters"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")

        client = HomelabClient(server_url="http://custom.local", api_key="custom-key")

        assert client.server_url == "http://custom.local"
        assert client.api_key == "custom-key"

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch.dict(
        os.environ,
        {"HOMELAB_SERVER_URL": "http://env.local", "HOMELAB_API_KEY": "env-key"},
    )
    def test_init_with_environment_variables(self, mock_exists, mock_home):
        """Test initialization with environment variables"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")

        client = HomelabClient()

        assert client.server_url == "http://env.local"
        assert client.api_key == "env-key"

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    def test_init_missing_server_url(self, mock_exists, mock_home):
        """Test initialization fails without server URL"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")

        with pytest.raises(ConfigurationError) as exc_info:
            HomelabClient()

        assert "Server URL not configured" in str(exc_info.value)

    @patch("homelab_client.config.Path.home")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"server_url": "http://test.local"}',
    )
    @patch("homelab_client.config.Path.exists")
    def test_init_missing_api_key(self, mock_exists, mock_file, mock_home):
        """Test initialization fails without API key"""
        mock_exists.return_value = True
        mock_home.return_value = Path("/home/test")

        with pytest.raises(ConfigurationError) as exc_info:
            HomelabClient()

        assert "API key not configured" in str(exc_info.value)
