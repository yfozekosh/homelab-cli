#!/usr/bin/env python3
"""
Unit tests for Homelab CLI Client
"""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

# Import the client
from homelab_client import HomelabClient


class TestPlugOperations:
    """Test plug-related operations"""

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.get")
    @patch("builtins.print")
    def test_list_plugs_success(self, mock_print, mock_get, mock_exists, mock_home):
        """Test listing plugs successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "plugs": {"plug1": {"ip": "192.168.1.10"}, "plug2": {"ip": "192.168.1.11"}}
        }
        mock_get.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.list_plugs()

        mock_get.assert_called_once()
        assert mock_print.call_count > 0

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.get")
    @patch("builtins.print")
    def test_list_plugs_empty(self, mock_print, mock_get, mock_exists, mock_home):
        """Test listing plugs when none configured"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.json.return_value = {"plugs": {}}
        mock_get.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.list_plugs()

        mock_print.assert_any_call("No plugs configured")

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.post")
    @patch("builtins.print")
    def test_add_plug_success(self, mock_print, mock_post, mock_exists, mock_home):
        """Test adding plug successfully"""
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
            client.add_plug("test-plug", "192.168.1.10")

        mock_post.assert_called_once()
        mock_print.assert_called_with("✓ Plug 'test-plug' added successfully")

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.put")
    @patch("builtins.print")
    def test_edit_plug_success(self, mock_print, mock_put, mock_exists, mock_home):
        """Test editing plug successfully"""
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
            client.edit_plug("test-plug", "192.168.1.20")

        mock_put.assert_called_once()
        args = mock_put.call_args
        assert args[1]["json"] == {"name": "test-plug", "ip": "192.168.1.20"}

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.delete")
    @patch("builtins.print")
    def test_remove_plug_success(self, mock_print, mock_delete, mock_exists, mock_home):
        """Test removing plug successfully"""
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
            client.remove_plug("test-plug")

        mock_delete.assert_called_once()
        mock_print.assert_called_with("✓ Plug 'test-plug' removed successfully")

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.post")
    def test_add_plug_error(self, mock_post, mock_exists, mock_home):
        """Test add plug with error"""
        from homelab_client import ConnectionError

        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            with pytest.raises(ConnectionError):
                client.add_plug("test-plug", "192.168.1.10")

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.post")
    @patch("builtins.print")
    def test_turn_on_plug_success(self, mock_print, mock_post, mock_exists, mock_home):
        """Test turning on a plug successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Plug 'test-plug' turned on"}
        mock_post.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.plug_on("test-plug")

        mock_post.assert_called_once_with(
            "http://test.local/plugs/test-plug/on",
            headers={"X-API-Key": "test-key"},
            json={},
            timeout=30,
        )
        mock_print.assert_called_with("✓ Plug 'test-plug' turned on")

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.post")
    @patch("builtins.print")
    def test_turn_off_plug_success(self, mock_print, mock_post, mock_exists, mock_home):
        """Test turning off a plug successfully"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Plug 'test-plug' turned off"}
        mock_post.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            client.plug_off("test-plug")

        mock_post.assert_called_once_with(
            "http://test.local/plugs/test-plug/off",
            headers={"X-API-Key": "test-key"},
            json={},
            timeout=30,
        )
        mock_print.assert_called_with("✓ Plug 'test-plug' turned off")

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.post")
    def test_turn_on_plug_not_found(self, mock_post, mock_exists, mock_home):
        """Test turning on a plug that does not exist"""
        from homelab_client import APIError

        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_post.return_value = mock_response

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            with pytest.raises(APIError):
                client.plug_on("nonexistent-plug")

    @patch("homelab_client.config.Path.home")
    @patch("homelab_client.config.Path.exists")
    @patch("homelab_client.api_client.requests.post")
    def test_turn_off_plug_connection_error(self, mock_post, mock_exists, mock_home):
        """Test turning off a plug with connection error"""
        from homelab_client import ConnectionError

        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with patch.dict(
            os.environ,
            {"HOMELAB_SERVER_URL": "http://test.local", "HOMELAB_API_KEY": "test-key"},
        ):
            client = HomelabClient()
            with pytest.raises(ConnectionError):
                client.plug_off("test-plug")
