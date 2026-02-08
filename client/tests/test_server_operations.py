#!/usr/bin/env python3
"""
Unit tests for Homelab CLI Client
"""

import os
from unittest.mock import Mock, patch
from pathlib import Path

# Import the client
from homelab_client import HomelabClient


class TestServerOperations:
    """Test server-related operations"""

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.get")
    @patch("builtins.print")
    def test_list_servers_success(self, mock_print, mock_get, mock_exists, mock_home):
        """Test listing servers successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.json.return_value = {
            "servers": {
                "server1": {
                    "hostname": "host1.local",
                    "mac": "00:11:22:33:44:55",
                    "plug": "plug1",
                    "ip": "192.168.1.100",
                    "online": True,
                }
            }
        }
        mock_get.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.list_servers()

        mock_get.assert_called_once()
        assert mock_print.call_count > 0

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.post")
    @patch("builtins.print")
    def test_add_server_success(self, mock_print, mock_post, mock_exists, mock_home):
        """Test adding server successfully"""
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
            client.add_server(
                "test-server", "host.local", mac="00:11:22:33:44:55", plug="plug1"
            )

        mock_post.assert_called_once()
        args = mock_post.call_args
        assert args[1]["json"]["name"] == "test-server"
        assert args[1]["json"]["hostname"] == "host.local"

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.post")
    @patch("builtins.print")
    def test_add_server_minimal(self, mock_print, mock_post, mock_exists, mock_home):
        """Test adding server with minimal parameters"""
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
            client.add_server("test-server", "host.local")

        args = mock_post.call_args
        assert args[1]["json"]["mac"] is None
        assert args[1]["json"]["plug"] is None

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.put")
    @patch("builtins.print")
    def test_edit_server_success(self, mock_print, mock_put, mock_exists, mock_home):
        """Test editing server successfully"""
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
                "test-server", hostname="newhost.local", mac="AA:BB:CC:DD:EE:FF"
            )

        mock_put.assert_called_once()
        args = mock_put.call_args
        assert args[1]["json"]["hostname"] == "newhost.local"
        assert args[1]["json"]["mac"] == "AA:BB:CC:DD:EE:FF"

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.delete")
    @patch("builtins.print")
    def test_remove_server_success(
        self, mock_print, mock_delete, mock_exists, mock_home
    ):
        """Test removing server successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.remove_server("test-server")

        mock_delete.assert_called_once()
