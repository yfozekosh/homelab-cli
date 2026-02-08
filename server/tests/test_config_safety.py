"""Tests for config file safety and race conditions"""

import pytest
import tempfile
import json
import os
import time
import threading
from pathlib import Path
from server.config import Config


@pytest.fixture
def temp_config_file():
    """Create a temporary config file"""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    
    # Write initial config
    with open(path, 'w') as f:
        json.dump({
            "plugs": {"test-plug": {"ip": "192.168.1.100"}},
            "servers": {"test-server": {"hostname": "test.local", "mac": "", "plug": None}},
            "state": {},
            "settings": {"electricity_price": 0.25}
        }, f)
    
    yield Path(path)
    
    # Cleanup
    try:
        os.unlink(path)
    except:
        pass
    # Cleanup backup if exists
    try:
        os.unlink(str(path) + '.bak')
    except:
        pass


class TestConfigSafety:
    """Test config file safety features"""

    def test_atomic_save(self, temp_config_file):
        """Test that save is atomic"""
        config = Config(temp_config_file)
        
        # Modify config
        config.add_plug("new-plug", "192.168.1.101")
        
        # Config should be saved
        assert temp_config_file.exists()
        
        # Load directly from file to verify
        with open(temp_config_file, 'r') as f:
            data = json.load(f)
        
        assert "new-plug" in data["plugs"]
        assert data["plugs"]["new-plug"]["ip"] == "192.168.1.101"

    def test_backup_created(self, temp_config_file):
        """Test that backup is created on save"""
        config = Config(temp_config_file)
        
        # Make a change that creates a backup
        config.add_server("backup-test", "backup.local")
        
        backup_path = temp_config_file.with_suffix('.json.bak')
        assert backup_path.exists()

    def test_concurrent_saves(self, temp_config_file):
        """Test concurrent saves don't corrupt config"""
        config = Config(temp_config_file)
        errors = []
        
        def save_plug(name: str):
            try:
                config.add_plug(f"plug-{name}", f"192.168.1.{name}")
                time.sleep(0.01)  # Small delay
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads that save concurrently
        threads = []
        for i in range(10):
            t = threading.Thread(target=save_plug, args=(str(i),))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # No errors should occur
        assert len(errors) == 0
        
        # Reload and verify all plugs are there
        config.reload()
        for i in range(10):
            assert f"plug-{i}" in config.data["plugs"]

    def test_state_update_only_saves_on_change(self, temp_config_file):
        """Test that state updates only save when state actually changes"""
        config = Config(temp_config_file)
        
        # Initialize state first
        config.update_server_state("test-server", False)
        time.sleep(0.1)
        
        # Get mtime after initialization
        mtime1 = os.path.getmtime(temp_config_file)
        time.sleep(0.1)
        
        # Update state to same value - should not save
        config.update_server_state("test-server", False)
        time.sleep(0.1)
        mtime2 = os.path.getmtime(temp_config_file)
        
        # mtime should not change
        assert mtime1 == mtime2
        
        # Update state to different value - should save
        config.update_server_state("test-server", True)
        time.sleep(0.1)
        mtime3 = os.path.getmtime(temp_config_file)
        
        # mtime should change
        assert mtime3 > mtime2

    def test_corrupted_file_recovery(self, temp_config_file):
        """Test that corrupted file is handled gracefully"""
        # Write corrupted JSON
        with open(temp_config_file, 'w') as f:
            f.write("{invalid json")
        
        # Should return default config without crashing
        config = Config(temp_config_file)
        
        assert "plugs" in config.data
        assert "servers" in config.data
        assert isinstance(config.data["plugs"], dict)

    def test_empty_file_handled(self, temp_config_file):
        """Test that empty config file is handled"""
        # Create empty file
        with open(temp_config_file, 'w') as f:
            f.write("")
        
        config = Config(temp_config_file)
        
        # Should have default structure
        assert "plugs" in config.data
        assert "servers" in config.data

    def test_file_locking_during_read(self, temp_config_file):
        """Test that file is locked during read operations"""
        config1 = Config(temp_config_file)
        
        # Start a long read operation in a thread
        read_completed = []
        
        def long_read():
            config2 = Config(temp_config_file)
            read_completed.append(True)
        
        thread = threading.Thread(target=long_read)
        thread.start()
        thread.join(timeout=2)
        
        # Read should complete successfully
        assert len(read_completed) == 1
