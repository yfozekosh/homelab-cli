"""Pytest configuration and fixtures for server blackbox tests"""

import pytest
import os
import sys
import tempfile
import shutil
import json
import time
import subprocess
from pathlib import Path
import requests

@pytest.fixture(scope="session")
def test_config_dir():
    """Create temporary directory for test configs"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture(scope="session")
def test_config_path(test_config_dir):
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
    return config_path

@pytest.fixture(scope="session")
def server_process(test_config_path):
    """Start test server"""
    env = os.environ.copy()
    env["CONFIG_PATH"] = str(test_config_path)
    env["API_KEY"] = "test-api-key"
    env["SSH_USER"] = "testuser"
    env["PYTHONUNBUFFERED"] = "1"
    
    # Run from parent directory so server module can be imported
    root_dir = Path(__file__).parent.parent.parent
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server.main:app", "--host", "127.0.0.1", "--port", "18000", "--log-level", "error"],
        cwd=root_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    # Wait for server
    for _ in range(60):
        try:
            response = requests.get("http://127.0.0.1:18000/health", timeout=1)
            if response.status_code == 200:
                break
        except:
            pass
        time.sleep(0.5)
    else:
        stdout, stderr = process.communicate(timeout=1)
        print(f"Server stdout: {stdout.decode()}")
        print(f"Server stderr: {stderr.decode()}")
        process.terminate()
        pytest.fail("Server failed to start")
    
    yield "http://127.0.0.1:18000"
    
    process.terminate()
    process.wait(timeout=5)

@pytest.fixture
def api_client(server_process):
    """HTTP client with authentication"""
    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url
            self.headers = {"X-API-Key": "test-api-key"}
        
        def get(self, path, **kwargs):
            return requests.get(f"{self.base_url}{path}", headers=self.headers, **kwargs)
        
        def post(self, path, **kwargs):
            return requests.post(f"{self.base_url}{path}", headers=self.headers, **kwargs)
        
        def put(self, path, **kwargs):
            return requests.put(f"{self.base_url}{path}", headers=self.headers, **kwargs)
        
        def delete(self, path, **kwargs):
            return requests.delete(f"{self.base_url}{path}", headers=self.headers, **kwargs)
    
    return APIClient(server_process)

@pytest.fixture
def unauthenticated_client(server_process):
    """HTTP client without authentication"""
    class UnauthClient:
        def __init__(self, base_url):
            self.base_url = base_url
        
        def get(self, path, **kwargs):
            return requests.get(f"{self.base_url}{path}", **kwargs)
        
        def post(self, path, **kwargs):
            return requests.post(f"{self.base_url}{path}", **kwargs)
    
    return UnauthClient(server_process)
