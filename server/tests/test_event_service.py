"""Tests for EventService"""

import pytest
from server.event_service import EventService


@pytest.fixture(autouse=True)
def clear_listeners():
    """Clear all event listeners before each test"""
    EventService.clear_listeners()
    yield
    EventService.clear_listeners()


class TestEventService:
    """Test EventService functionality"""

    @pytest.mark.asyncio
    async def test_add_listener(self):
        """Test adding a listener"""
        callback_called = []

        async def callback(data):
            callback_called.append(data)

        EventService.add_listener("test_event", callback)
        await EventService.emit("test_event", {"message": "hello"})

        assert len(callback_called) == 1
        assert callback_called[0] == {"message": "hello"}

    @pytest.mark.asyncio
    async def test_multiple_listeners(self):
        """Test multiple listeners for the same event"""
        callback1_called = []
        callback2_called = []

        async def callback1(data):
            callback1_called.append(data)

        async def callback2(data):
            callback2_called.append(data)

        EventService.add_listener("test_event", callback1)
        EventService.add_listener("test_event", callback2)
        
        await EventService.emit("test_event", {"count": 1})

        assert len(callback1_called) == 1
        assert len(callback2_called) == 1
        assert callback1_called[0] == {"count": 1}
        assert callback2_called[0] == {"count": 1}

    @pytest.mark.asyncio
    async def test_emit_without_listeners(self):
        """Test emitting an event with no listeners"""
        # Should not raise an error
        await EventService.emit("non_existent_event", {"data": "test"})

    @pytest.mark.asyncio
    async def test_listener_exception_handling(self):
        """Test that exceptions in listeners don't break other listeners"""
        callback1_called = []
        callback2_called = []

        async def callback1(data):
            callback1_called.append(data)
            raise ValueError("Test error")

        async def callback2(data):
            callback2_called.append(data)

        EventService.add_listener("test_event", callback1)
        EventService.add_listener("test_event", callback2)
        
        # Should not raise, callback2 should still be called
        await EventService.emit("test_event", {"test": "data"})

        assert len(callback1_called) == 1
        assert len(callback2_called) == 1

    @pytest.mark.asyncio
    async def test_clear_specific_listener(self):
        """Test clearing listeners for a specific event"""
        callback_called = []

        async def callback(data):
            callback_called.append(data)

        EventService.add_listener("event1", callback)
        EventService.add_listener("event2", callback)
        
        EventService.clear_listeners("event1")
        
        await EventService.emit("event1", {"data": 1})
        await EventService.emit("event2", {"data": 2})

        # Only event2 should have triggered
        assert len(callback_called) == 1
        assert callback_called[0] == {"data": 2}

    @pytest.mark.asyncio
    async def test_clear_all_listeners(self):
        """Test clearing all listeners"""
        callback_called = []

        async def callback(data):
            callback_called.append(data)

        EventService.add_listener("event1", callback)
        EventService.add_listener("event2", callback)
        
        EventService.clear_listeners()
        
        await EventService.emit("event1", {"data": 1})
        await EventService.emit("event2", {"data": 2})

        # No callbacks should have been triggered
        assert len(callback_called) == 0

    @pytest.mark.asyncio
    async def test_multiple_emissions(self):
        """Test emitting the same event multiple times"""
        callback_called = []

        async def callback(data):
            callback_called.append(data)

        EventService.add_listener("test_event", callback)
        
        await EventService.emit("test_event", {"count": 1})
        await EventService.emit("test_event", {"count": 2})
        await EventService.emit("test_event", {"count": 3})

        assert len(callback_called) == 3
        assert callback_called[0] == {"count": 1}
        assert callback_called[1] == {"count": 2}
        assert callback_called[2] == {"count": 3}

    @pytest.mark.asyncio
    async def test_different_data_types(self):
        """Test emitting events with different data types"""
        callback_called = []

        async def callback(data):
            callback_called.append(data)

        EventService.add_listener("test_event", callback)
        
        # Test different data types
        await EventService.emit("test_event", "string")
        await EventService.emit("test_event", 123)
        await EventService.emit("test_event", [1, 2, 3])
        await EventService.emit("test_event", {"key": "value"})
        await EventService.emit("test_event", None)

        assert len(callback_called) == 5
        assert callback_called[0] == "string"
        assert callback_called[1] == 123
        assert callback_called[2] == [1, 2, 3]
        assert callback_called[3] == {"key": "value"}
        assert callback_called[4] is None
