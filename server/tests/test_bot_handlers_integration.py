"""Integration tests for bot handlers and event service"""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from server.bot.handlers import BotHandlers
from server.dependencies import ServiceContainer
from server.event_service import EventService


@pytest.fixture
def temp_config():
    """Create a temporary config file"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(
            {
                "plugs": {},
                "servers": {},
                "state": {},
                "settings": {"electricity_price": 0.0},
            },
            f,
        )
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
def service_container(mock_env):
    """Create a service container"""
    ServiceContainer.reset()
    container = ServiceContainer.get_instance()
    yield container
    ServiceContainer.reset()


class TestBotHandlersEventIntegration:
    """Test BotHandlers integration with EventService"""

    def test_register_listeners_adds_handler(self, service_container):
        """BotHandlers.register_listeners registers the status_update listener"""
        allowed_users = [123456]
        handlers = BotHandlers(service_container, allowed_users)
        handlers.register_listeners()

        event_svc = service_container.event_service
        assert "status_update" in event_svc._listeners
        assert len(event_svc._listeners["status_update"]) == 1

    @pytest.mark.asyncio
    async def test_event_service_can_emit_to_handler(self, service_container):
        """EventService can emit events to handler"""
        allowed_users = [123456]
        handler_called = []

        handlers = BotHandlers(service_container, allowed_users)

        async def mock_handle(updateObj):
            handler_called.append(updateObj)

        handlers.handle_status_update = mock_handle
        handlers.register_listeners()

        test_data = {"server": "test-server", "status": "online"}
        await service_container.event_service.emit("status_update", test_data)

        assert len(handler_called) == 1
        assert handler_called[0] == test_data

    def test_event_service_has_correct_method_names(self):
        """EventService has the expected method names"""
        assert hasattr(EventService, "add_listener")
        assert hasattr(EventService, "emit")
        assert hasattr(EventService, "clear_listeners")
        assert not hasattr(EventService, "addListener")
        assert not hasattr(EventService, "clearListeners")

    @pytest.mark.asyncio
    async def test_multiple_handlers_can_register(self, service_container):
        """Multiple handlers can register for the same event"""
        allowed_users = [123456]
        event_svc = service_container.event_service

        handlers1 = BotHandlers(service_container, allowed_users)
        handlers1.register_listeners()
        handlers2 = BotHandlers(service_container, allowed_users)
        handlers2.register_listeners()

        assert len(event_svc._listeners["status_update"]) == 2

    def test_container_provides_event_service(self, service_container):
        """Container provides EventService instance"""
        assert hasattr(service_container, "event_service")
        assert service_container.event_service is not None
        assert isinstance(service_container.event_service, EventService)

    @pytest.mark.asyncio
    async def test_constructor_does_not_register(self, service_container):
        """Constructor alone does NOT register listeners"""
        allowed_users = [123456]
        handlers = BotHandlers(service_container, allowed_users)
        # Without register_listeners(), no listeners are added
        event_svc = service_container.event_service
        assert "status_update" not in event_svc._listeners
