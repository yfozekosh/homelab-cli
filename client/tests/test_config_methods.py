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


class TestConfigMethods:
    """Test configuration loading and saving"""

    @patch("homelab_client.config.Path.home")
    @patch("builtins.open", new_callable=mock_open)
    @patch("homelab_client.config.Path.exists")
    def test_load_config_success(self, mock_exists, mock_file, mock_home):
        """Test successful config loading"""
        mock_exists.return_value = True
        mock_home.return_value = Path("/home/test")
        config_data = '{"server_url": "http://test.local", "api_key": "test-key"}'
        mock_file.return_value.read.return_value = config_data

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://env.local", "HOMELAB_API_KEY": "env-key"},
        ):
            client = HomelabClient()
            config = client._load_config()

        assert "server_url" in config
        assert "api_key" in config

    @patch("homelab_client.config.Path.home")
    @patch("builtins.open", new_callable=mock_open, read_data="invalid json")
    @patch("homelab_client.config.Path.exists")
    def test_load_config_invalid_json(self, mock_exists, mock_file, mock_home):
        """Test config loading with invalid JSON"""
        mock_exists.return_value = True
        mock_home.return_value = Path("/home/test")

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://env.local", "HOMELAB_API_KEY": "env-key"},
        ):
            client = HomelabClient()
            config = client._load_config()

        assert config == {}

    @patch("homelab_client.config.Path.home")
    @patch("builtins.open", new_callable=mock_open)
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.config.Path.mkdir")
    def test_save_config(self, mock_mkdir, mock_exists, mock_file, mock_home):
        """Test config saving"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://env.local", "HOMELAB_API_KEY": "env-key"},
        ):
            client = HomelabClient()
            client._save_config(
                {"server_url": "http://new.local", "api_key": "new-key"}
            )

        mock_mkdir.assert_called_once()
        mock_file.assert_called()
