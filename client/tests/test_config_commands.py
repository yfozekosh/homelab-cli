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
from lab import HomelabClient


class TestConfigCommands:
    """Test configuration commands"""
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('lab.Path.mkdir')
    @patch('builtins.print')
    def test_set_server_url(self, mock_print, mock_mkdir, mock_file, mock_exists, mock_home):
        """Test setting server URL"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.set_server_url("http://newserver.local")
        
        mock_print.assert_called_with("✓ Server URL set to: http://newserver.local")
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('lab.Path.mkdir')
    @patch('builtins.print')
    def test_set_api_key(self, mock_print, mock_mkdir, mock_file, mock_exists, mock_home):
        """Test setting API key"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            client.set_api_key("new-api-key")
        
        mock_print.assert_called_with("✓ API key saved")

