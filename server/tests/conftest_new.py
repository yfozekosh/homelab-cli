"""Pytest configuration with in-process server for coverage"""

import pytest
import os
import tempfile
import shutil
import json
from pathlib import Path
from fastapi.testclient import TestClient

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up environment variables for testing"""
    os.environ["API_KEY"] = "test-api-key"
    os.environ["SSH_USER"] = "testuser"
    os.environ["TAPO_USERNAME"] = "test@example.com"
    os.environ["TAPO_PASSWORD"] = "test-password"

@pytest.fixture(scope="session")
def test_config_dir():
    """Create temporary directory for test configs"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="session")
def test_config_path(test_config_dir, setup_test_env):
    """Path to test config file"""
    config_path = Path(test_config_dir) / "test_config.json"
    config_data = {
        "plugs": {
            "test-plug": {"ip": "192.168.1.100"},
            "main-srv-plug": {"ip": "192.168.1.101"},
        },
        "servers": {
            "test-server": {
                "hostname": "192.168.1.107",
                "mac": "AA:BB:CC:DD:EE:FF",
                "plug": "test-plug",
            }
        },
        "electricity_price": 0.25,
    }
    with open(config_path, "w") as f:
        json.dump(config_data, f)
    
    # Set CONFIG_PATH before importing server
    os.environ["CONFIG_PATH"] = str(config_path)
    return config_path

@pytest.fixture(scope="session")
def app(test_config_path):
    """Get FastAPI app instance"""
    from server.main import app
    return app

@pytest.fixture(scope="session")
def client(app):
    """Get TestClient for making requests"""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def api_client(client):
    """HTTP client with authentication"""
    class APIClient:
        def __init__(self, test_client):
            self.client = test_client
            self.headers = {"X-API-Key": "test-api-key"}
        
        def get(self, path, **kwargs):
            kwargs.setdefault("headers", {}).update(self.headers)
            return self.client.get(path, **kwargs)
        
        def post(self, path, **kwargs):
            kwargs.setdefault("headers", {}).update(self.headers)
            return self.client.post(path, **kwargs)
        
        def put(self, path, **kwargs):
            kwargs.setdefault("headers", {}).update(self.headers)
            return self.client.put(path, **kwargs)
        
        def delete(self, path, **kwargs):
            kwargs.setdefault("headers", {}).update(self.headers)
            return self.client.delete(path, **kwargs)
    
    return APIClient(client)

@pytest.fixture
def unauthenticated_client(client):
    """HTTP client without authentication"""
    return client
