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


class TestMainFunction:
    """Test main() CLI entry point"""
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'plug', 'list'])
    def test_main_plug_list(self, mock_exists, mock_home):
        """Test main with plug list command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'list_plugs') as mock_list:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_list.assert_called_once()
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'server', 'list'])
    def test_main_server_list(self, mock_exists, mock_home):
        """Test main with server list command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'list_servers') as mock_list:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_list.assert_called_once()
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'on', 'test-server'])
    def test_main_power_on(self, mock_exists, mock_home):
        """Test main with power on command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'power_on') as mock_power_on:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_power_on.assert_called_once_with('test-server')
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'off', 'test-server'])
    def test_main_power_off(self, mock_exists, mock_home):
        """Test main with power off command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'power_off') as mock_power_off:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_power_off.assert_called_once_with('test-server')
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'status'])
    def test_main_status(self, mock_exists, mock_home):
        """Test main with status command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'get_status') as mock_status:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_status.assert_called_once_with(follow_interval=None)
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'status', '-f'])
    def test_main_status_follow_default(self, mock_exists, mock_home):
        """Test main with status follow (default interval)"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'get_status') as mock_status:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_status.assert_called_once_with(follow_interval=5.0)
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'status', '-f', '2.5'])
    def test_main_status_follow_custom_interval(self, mock_exists, mock_home):
        """Test main with status follow custom interval"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'get_status') as mock_status:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_status.assert_called_once_with(follow_interval=2.5)
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'set', 'price', '0.25'])
    def test_main_set_price(self, mock_exists, mock_home):
        """Test main with set price command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'set_electricity_price') as mock_set:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_set.assert_called_once_with(0.25)
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'get', 'price'])
    def test_main_get_price(self, mock_exists, mock_home):
        """Test main with get price command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'get_electricity_price') as mock_get:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_get.assert_called_once()
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'plug', 'add', 'new-plug', '192.168.1.50'])
    def test_main_plug_add(self, mock_exists, mock_home):
        """Test main with plug add command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'add_plug') as mock_add:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_add.assert_called_once_with('new-plug', '192.168.1.50')
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'server', 'add', 'new-server', 'host.local', '00:11:22:33:44:55', 'plug1'])
    def test_main_server_add_full(self, mock_exists, mock_home):
        """Test main with server add command (all params)"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'add_server') as mock_add:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        mock_add.assert_called_once_with('new-server', 'host.local', '00:11:22:33:44:55', 'plug1')
    
    @patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'})
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('sys.argv', ['lab', 'server', 'edit', 'test-server', '--hostname', 'newhost.local'])
    def test_main_server_edit(self, mock_exists, mock_home):
        """Test main with server edit command"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.object(HomelabClient, 'edit_server') as mock_edit:
            with patch.object(HomelabClient, 'health_check', return_value=True):
                from lab import main
                main()
        
        # Check it was called with name and hostname
        assert mock_edit.called
        args, kwargs = mock_edit.call_args
        assert args[0] == 'test-server'
        assert 'hostname' in kwargs or (len(args) > 1 and args[1] == 'newhost.local')
    
    @patch('sys.argv', ['lab'])
    def test_main_no_command(self):
        """Test main with no command shows help"""
        from lab import main
        # Should return without error
        result = main()
        # Function returns None on help
        assert result is None


