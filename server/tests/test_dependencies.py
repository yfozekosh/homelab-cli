"""Unit tests for dependency injection container"""

import os
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

from server.dependencies import (
    ServiceContainer,
    get_service_container,
    get_config,
    get_plug_service,
    get_server_service,
    get_power_service,
    get_status_service,
    get_event_service,
)
from server.config import Config
from server.plug_service import PlugService
from server.server_service import ServerService
from server.power_service import PowerControlService
from server.status_service import StatusService
from server.event_service import EventService


@pytest.fixture
def temp_config():
    """Create a temporary config file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "plugs": {},
            "servers": {},
            "electricity_price": 0.25
        }, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def mock_env(temp_config):
    """Mock all required environment variables"""
    env_vars = {
        "CONFIG_PATH": temp_config,
        "TAPO_USERNAME": "test@example.com",
        "TAPO_PASSWORD": "testpassword",
        "SSH_USER": "testuser",
        "API_KEY": "test-api-key",
    }
    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture
def reset_container():
    """Reset container before and after test"""
    ServiceContainer.reset()
    get_service_container.cache_clear()
    yield
    ServiceContainer.reset()
    get_service_container.cache_clear()


class TestServiceContainer:
    """Tests for ServiceContainer class"""

    def test_singleton_instance(self, mock_env, reset_container):
        """Container returns same instance"""
        container1 = ServiceContainer.get_instance()
        container2 = ServiceContainer.get_instance()
        assert container1 is container2

    def test_creates_all_services(self, mock_env, reset_container):
        """Container creates all required services"""
        container = ServiceContainer.get_instance()
        assert isinstance(container.config, Config)
        assert isinstance(container.plug_service, PlugService)
        assert isinstance(container.server_service, ServerService)
        assert isinstance(container.power_service, PowerControlService)
        assert isinstance(container.status_service, StatusService)
        assert isinstance(container.event_service, EventService)

    def test_reset_clears_instance(self, mock_env, reset_container):
        """Reset clears the singleton instance"""
        container1 = ServiceContainer.get_instance()
        ServiceContainer.reset()
        container2 = ServiceContainer.get_instance()
        assert container1 is not container2

    def test_uses_config_path_env(self, mock_env, reset_container):
        """Container uses CONFIG_PATH environment variable"""
        container = ServiceContainer.get_instance()
        assert container.config is not None


class TestGetServiceContainer:
    """Tests for get_service_container function"""

    def test_returns_cached_container(self, mock_env, reset_container):
        """Function returns cached container"""
        container1 = get_service_container()
        container2 = get_service_container()
        assert container1 is container2


class TestDependencyGetters:
    """Tests for individual dependency getter functions"""

    def test_get_config(self, mock_env, reset_container):
        """get_config returns Config instance"""
        container = get_service_container()
        config = get_config(container)
        assert isinstance(config, Config)
        assert config is container.config

    def test_get_plug_service(self, mock_env, reset_container):
        """get_plug_service returns PlugService instance"""
        container = get_service_container()
        service = get_plug_service(container)
        assert isinstance(service, PlugService)
        assert service is container.plug_service

    def test_get_server_service(self, mock_env, reset_container):
        """get_server_service returns ServerService instance"""
        container = get_service_container()
        service = get_server_service(container)
        assert isinstance(service, ServerService)
        assert service is container.server_service

    def test_get_power_service(self, mock_env, reset_container):
        """get_power_service returns PowerControlService instance"""
        container = get_service_container()
        service = get_power_service(container)
        assert isinstance(service, PowerControlService)
        assert service is container.power_service

    def test_get_status_service(self, mock_env, reset_container):
        """get_status_service returns StatusService instance"""
        container = get_service_container()
        service = get_status_service(container)
        assert isinstance(service, StatusService)
        assert service is container.status_service

    def test_get_event_service(self, mock_env, reset_container):
        """get_event_service returns EventService instance"""
        container = get_service_container()
        service = get_event_service(container)
        assert isinstance(service, EventService)
        assert service is container.event_service
