"""Tests for EventService"""

import pytest

from server.event_service import EventService


@pytest.fixture()
def event_service():
    """Fresh EventService instance per test"""
    return EventService()


class TestEventService:
    """Test EventService functionality"""

    @pytest.mark.asyncio
    async def test_add_listener(self, event_service):
        """Test adding a listener"""
        callback_called = []

        async def callback(data):
            callback_called.append(data)

        event_service.add_listener("test_event", callback)
        await event_service.emit("test_event", {"message": "hello"})

        assert len(callback_called) == 1
        assert callback_called[0] == {"message": "hello"}

    @pytest.mark.asyncio
    async def test_multiple_listeners(self, event_service):
        """Test multiple listeners for the same event"""
        callback1_called = []
        callback2_called = []

        async def callback1(data):
            callback1_called.append(data)

        async def callback2(data):
            callback2_called.append(data)

        event_service.add_listener("test_event", callback1)
        event_service.add_listener("test_event", callback2)

        await event_service.emit("test_event", {"count": 1})

        assert len(callback1_called) == 1
        assert len(callback2_called) == 1
        assert callback1_called[0] == {"count": 1}
        assert callback2_called[0] == {"count": 1}

    @pytest.mark.asyncio
    async def test_emit_without_listeners(self, event_service):
        """Test emitting an event with no listeners"""
        # Should not raise an error
        await event_service.emit("non_existent_event", {"data": "test"})

    @pytest.mark.asyncio
    async def test_listener_exception_handling(self, event_service):
        """Test that exceptions in listeners don't break other listeners"""
        callback1_called = []
        callback2_called = []

        async def callback1(data):
            callback1_called.append(data)
            raise ValueError("Test error")

        async def callback2(data):
            callback2_called.append(data)

        event_service.add_listener("test_event", callback1)
        event_service.add_listener("test_event", callback2)

        # Should not raise, callback2 should still be called
        await event_service.emit("test_event", {"test": "data"})

        assert len(callback1_called) == 1
        assert len(callback2_called) == 1

    @pytest.mark.asyncio
    async def test_clear_specific_listener(self, event_service):
        """Test clearing listeners for a specific event"""
        callback_called = []

        async def callback(data):
            callback_called.append(data)

        event_service.add_listener("event1", callback)
        event_service.add_listener("event2", callback)

        event_service.clear_listeners("event1")

        await event_service.emit("event1", {"data": 1})
        await event_service.emit("event2", {"data": 2})

        # Only event2 should have triggered
        assert len(callback_called) == 1
        assert callback_called[0] == {"data": 2}

    @pytest.mark.asyncio
    async def test_clear_all_listeners(self, event_service):
        """Test clearing all listeners"""
        callback_called = []

        async def callback(data):
            callback_called.append(data)

        event_service.add_listener("event1", callback)
        event_service.add_listener("event2", callback)

        event_service.clear_listeners()

        await event_service.emit("event1", {"data": 1})
        await event_service.emit("event2", {"data": 2})

        # No callbacks should have been triggered
        assert len(callback_called) == 0

    @pytest.mark.asyncio
    async def test_multiple_emissions(self, event_service):
        """Test emitting the same event multiple times"""
        callback_called = []

        async def callback(data):
            callback_called.append(data)

        event_service.add_listener("test_event", callback)

        await event_service.emit("test_event", {"count": 1})
        await event_service.emit("test_event", {"count": 2})
        await event_service.emit("test_event", {"count": 3})

        assert len(callback_called) == 3
        assert callback_called[0] == {"count": 1}
        assert callback_called[1] == {"count": 2}
        assert callback_called[2] == {"count": 3}

    @pytest.mark.asyncio
    async def test_different_data_types(self, event_service):
        """Test emitting events with different data types"""
        callback_called = []

        async def callback(data):
            callback_called.append(data)

        event_service.add_listener("test_event", callback)

        # Test different data types
        await event_service.emit("test_event", "string")
        await event_service.emit("test_event", 123)
        await event_service.emit("test_event", [1, 2, 3])
        await event_service.emit("test_event", {"key": "value"})
        await event_service.emit("test_event", None)

        assert len(callback_called) == 5
        assert callback_called[0] == "string"
        assert callback_called[1] == 123
        assert callback_called[2] == [1, 2, 3]
        assert callback_called[3] == {"key": "value"}
        assert callback_called[4] is None

    @pytest.mark.asyncio
    async def test_instances_are_isolated(self):
        """Test that separate EventService instances don't share listeners"""
        svc1 = EventService()
        svc2 = EventService()

        calls1 = []
        calls2 = []

        svc1.add_listener("evt", lambda data: calls1.append(data))
        svc2.add_listener("evt", lambda data: calls2.append(data))

        await svc1.emit("evt", "from1")
        assert len(calls1) == 1
        assert len(calls2) == 0  # svc2 must not see svc1's event
