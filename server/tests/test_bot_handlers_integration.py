"""Integration tests for bot handlers and event service"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import json
import os

from server.bot.handlers import BotHandlers
from server.dependencies import ServiceContainer
from server.event_service import EventService


@pytest.fixture
def temp_config():
    """Create a temporary config file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "plugs": {},
            "servers": {},
            "state": {},
            "settings": {"electricity_price": 0.0}
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
def service_container(mock_env):
    """Create a service container"""
    ServiceContainer.reset()
    container = ServiceContainer.get_instance()
    yield container
    ServiceContainer.reset()


@pytest.fixture(autouse=True)
def clear_event_listeners():
    """Clear all event listeners before and after each test"""
    EventService.clear_listeners()
    yield
    EventService.clear_listeners()


class TestBotHandlersEventIntegration:
    """Test BotHandlers integration with EventService"""

    def test_handlers_registers_event_listener(self, service_container):
        """Test that BotHandlers registers event listener on init"""
        allowed_users = [123456]
        
        # Create handlers - this should register the listener
        handlers = BotHandlers(service_container, allowed_users)
        
        # Verify listener was registered
        assert "status_update" in EventService.listeners
        assert len(EventService.listeners["status_update"]) == 1
        
    @pytest.mark.asyncio
    async def test_event_service_can_emit_to_handler(self, service_container):
        """Test that EventService can emit events to handler"""
        allowed_users = [123456]
        handler_called = []
        
        # Create handlers
        handlers = BotHandlers(service_container, allowed_users)
        
        # Mock the handle_status_update method
        async def mock_handle(updateObj):
            handler_called.append(updateObj)
        
        handlers.handle_status_update = mock_handle
        
        # Re-register with mocked method
        EventService.clear_listeners("status_update")
        EventService.add_listener("status_update", handlers.handle_status_update)
        
        # Emit event
        test_data = {"server": "test-server", "status": "online"}
        await EventService.emit("status_update", test_data)
        
        # Verify handler was called
        assert len(handler_called) == 1
        assert handler_called[0] == test_data

    def test_event_service_has_correct_method_names(self):
        """Test that EventService has the expected method names (snake_case)"""
        # Verify correct method names exist
        assert hasattr(EventService, 'add_listener')
        assert hasattr(EventService, 'emit')
        assert hasattr(EventService, 'clear_listeners')
        
        # Verify old camelCase names don't exist
        assert not hasattr(EventService, 'addListener')
        assert not hasattr(EventService, 'clearListeners')

    @pytest.mark.asyncio
    async def test_multiple_handlers_can_register(self, service_container):
        """Test that multiple handlers can register for the same event"""
        allowed_users = [123456]
        
        # Create two handler instances
        handlers1 = BotHandlers(service_container, allowed_users)
        handlers2 = BotHandlers(service_container, allowed_users)
        
        # Both should have registered
        assert len(EventService.listeners["status_update"]) == 2

    def test_container_provides_event_service(self, service_container):
        """Test that container provides EventService instance"""
        assert hasattr(service_container, 'event_service')
        assert service_container.event_service is not None
        from server.event_service import EventService
        # EventService is instantiated, so check it's an instance of the class
        assert isinstance(service_container.event_service, EventService)
