"""Unit tests for Config class"""
import pytest
import json
import tempfile
from pathlib import Path

def test_config_initialization():
    """Test config initialization"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test.json"
        from server.config import Config
        config = Config(config_path)
        assert config.config_path == config_path

def test_config_load_creates_default():
    """Test that initializing with non-existent config creates default data"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "new.json"
        from server.config import Config
        config = Config(config_path)
        # Config loads default data automatically in __init__
        assert "plugs" in config.data
        assert "servers" in config.data
        assert "settings" in config.data
        # File created on first save
        config.save()
        assert config_path.exists()

def test_config_save_and_load():
    """Test saving and loading config"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test.json"
        from server.config import Config
        
        # Create and save
        config1 = Config(config_path)
        config1.data["plugs"] = {"test": {"ip": "192.168.1.1"}}
        config1.save()
        
        # Load in new instance (loads automatically in __init__)
        config2 = Config(config_path)
        assert "test" in config2.data["plugs"]
        assert config2.data["plugs"]["test"]["ip"] == "192.168.1.1"

def test_config_get_plugs():
    """Test getting plugs from config"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test.json"
        from server.config import Config
        config = Config(config_path)
        config.data["plugs"] = {"p1": {"ip": "1.1.1.1"}, "p2": {"ip": "2.2.2.2"}}
        plugs = config.data.get("plugs", {})
        assert len(plugs) == 2
        assert "p1" in plugs
        assert "p2" in plugs

def test_config_add_plug():
    """Test adding a plug"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test.json"
        from server.config import Config
        config = Config(config_path)
        config.add_plug("new-plug", "10.0.0.1")
        assert "new-plug" in config.data["plugs"]
        assert config.data["plugs"]["new-plug"]["ip"] == "10.0.0.1"

def test_config_remove_plug():
    """Test removing a plug"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test.json"
        from server.config import Config
        config = Config(config_path)
        config.add_plug("remove-me", "10.0.0.1")
        assert "remove-me" in config.data["plugs"]
        config.remove_plug("remove-me")
        assert "remove-me" not in config.data["plugs"]

def test_config_edit_plug():
    """Test editing a plug"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test.json"
        from server.config import Config
        config = Config(config_path)
        config.data["plugs"]["edit-me"] = {"ip": "10.0.0.1"}
        config.data["plugs"]["edit-me"]["ip"] = "10.0.0.2"
        assert config.data["plugs"]["edit-me"]["ip"] == "10.0.0.2"

def test_config_get_servers():
    """Test getting servers from config"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test.json"
        from server.config import Config
        config = Config(config_path)
        config.data["servers"] = {
            "s1": {"hostname": "host1", "mac": "AA:BB:CC:DD:EE:FF", "plug": "p1"}
        }
        servers = config.data.get("servers", {})
        assert len(servers) == 1
        assert "s1" in servers

def test_config_add_server():
    """Test adding a server"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test.json"
        from server.config import Config
        config = Config(config_path)
        config.data["servers"]["srv1"] = {
            "hostname": "192.168.1.100",
            "mac": "AA:BB:CC:DD:EE:FF",
            "plug": "plug1"
        }
        assert "srv1" in config.data["servers"]
        assert config.data["servers"]["srv1"]["hostname"] == "192.168.1.100"

def test_config_remove_server():
    """Test removing a server"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test.json"
        from server.config import Config
        config = Config(config_path)
        config.data["servers"]["del-srv"] = {
            "hostname": "192.168.1.100",
            "mac": "AA:BB:CC:DD:EE:FF",
            "plug": "plug1"
        }
        del config.data["servers"]["del-srv"]
        assert "del-srv" not in config.data["servers"]

def test_config_set_electricity_price():
    """Test setting electricity price"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test.json"
        from server.config import Config
        config = Config(config_path)
        config.data["settings"]["electricity_price"] = 0.35
        assert config.data["settings"]["electricity_price"] == 0.35

def test_config_get_electricity_price():
    """Test getting electricity price"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "test.json"
        from server.config import Config
        config = Config(config_path)
        config.data["settings"]["electricity_price"] = 0.40
        assert config.get_electricity_price() == 0.40
