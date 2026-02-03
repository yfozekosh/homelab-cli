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


class TestElectricityPrice:
    """Test electricity price operations"""

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.post")
    @patch("builtins.print")
    def test_set_electricity_price_success(
        self, mock_print, mock_post, mock_exists, mock_home
    ):
        """Test setting electricity price"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.set_electricity_price(0.25)

        args = mock_post.call_args
        assert args[1]["json"]["price"] == 0.25

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.get")
    @patch("builtins.print")
    def test_get_electricity_price_success(
        self, mock_print, mock_get, mock_exists, mock_home
    ):
        """Test getting electricity price"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"price": 0.25}
        mock_get.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.get_electricity_price()

        assert any("0.25" in str(call) for call in mock_print.call_args_list)

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.get")
    @patch("builtins.print")
    def test_get_electricity_price_not_set(
        self, mock_print, mock_get, mock_exists, mock_home
    ):
        """Test getting electricity price when not set"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"price": 0}
        mock_get.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.get_electricity_price()

        assert any(
            "No electricity price set" in str(call)
            for call in mock_print.call_args_list
        )
