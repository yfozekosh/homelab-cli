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


class TestWaitForInput:
    """Test keyboard input waiting functionality"""
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.os.name', 'posix')
    @patch('select.select')
    @patch('sys.stdin')
    @patch('time.sleep')
    def test_wait_for_input_q_pressed(self, mock_sleep, mock_stdin, mock_select, mock_exists, mock_home):
        """Test wait for input when 'q' is pressed"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_select.return_value = ([mock_stdin], [], [])
        mock_stdin.read.return_value = 'q'
        
        stop_event = threading.Event()
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            result = client._wait_for_input(0.1, stop_event)
        
        # Should return False when 'q' is pressed
        assert result is False
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.os.name', 'posix')
    @patch('select.select')
    @patch('sys.stdin')
    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_input_timeout(self, mock_time, mock_sleep, mock_stdin, mock_select, mock_exists, mock_home):
        """Test wait for input timeout"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        # Simulate time progressing beyond interval
        mock_time.side_effect = [0, 0.05, 0.2]  # Start, during loop, after interval
        mock_select.return_value = ([], [], [])
        
        stop_event = threading.Event()
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            result = client._wait_for_input(0.1, stop_event)
        
        # Should return True when timeout is reached
        assert result is True
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    @patch('lab.os.name', 'posix')
    @patch('select.select')
    @patch('sys.stdin')
    @patch('time.sleep')
    def test_wait_for_input_stop_event(self, mock_sleep, mock_stdin, mock_select, mock_exists, mock_home):
        """Test wait for input with stop event"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        mock_select.return_value = ([], [], [])
        
        stop_event = threading.Event()
        stop_event.set()  # Set event immediately
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            result = client._wait_for_input(5.0, stop_event)
        
        # Should return False when stop_event is set
        assert result is False
    
    @patch('lab.Path.home')
    @patch('lab.Path.exists')
    def test_wait_for_input_method_exists(self, mock_exists, mock_home):
        """Test wait for input method exists"""
        mock_exists.return_value = False
        mock_home.return_value = Path("/home/test")
        
        with patch.dict(os.environ, {'HOMELAB_SERVER_URL': 'http://test.local', 'HOMELAB_API_KEY': 'test-key'}):
            client = HomelabClient()
            assert hasattr(client, '_wait_for_input')

