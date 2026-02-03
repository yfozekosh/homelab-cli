"""
Shared pytest fixtures and configuration for homelab client tests
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path so we can import lab module
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_home(monkeypatch):
    """Mock Path.home() to return test directory"""
    test_home = Path("/home/test")
    monkeypatch.setattr(Path, "home", lambda: test_home)
    return test_home


@pytest.fixture
def mock_exists():
    """Mock Path.exists() to return False by default"""
    with patch('lab.Path.exists') as mock:
        mock.return_value = False
        yield mock


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for tests"""
    env = {
        'HOMELAB_SERVER_URL': 'http://test.local',
        'HOMELAB_API_KEY': 'test-key'
    }
    with patch.dict(os.environ, env):
        yield env


@pytest.fixture
def mock_http_response():
    """Create a mock HTTP response"""
    def _create_response(status_code=200, json_data=None):
        response = Mock()
        response.status_code = status_code
        if json_data:
            response.json.return_value = json_data
        return response
    return _create_response
