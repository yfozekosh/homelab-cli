"""Event service for handling events between services"""

import logging
from typing import Dict, List, Callable, Any

logger = logging.getLogger(__name__)


class EventService:
    """Moves events between services and handles event processing"""

    listeners: Dict[str, List[Callable]] = {}

    @classmethod
    def add_listener(cls, event_name: str, callback: Callable) -> None:
        """Add a listener for an event"""
        logger.debug(f"Adding listener for event: {event_name}")
        events = cls.listeners.setdefault(event_name, [])
        events.append(callback)

    @classmethod
    async def emit(cls, event_name: str, data: Any) -> None:
        """Emit an event to all listeners"""
        logger.info(f"Emitting event: {event_name}")
        logger.debug(f"Event data: {data}")
        listeners = cls.listeners.get(event_name, [])
        for callback in listeners:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"Error in event listener for {event_name}: {e}", exc_info=True)

    @classmethod
    def clear_listeners(cls, event_name: str | None = None) -> None:
        """Clear listeners for a specific event or all events"""
        if event_name:
            cls.listeners.pop(event_name, None)
        else:
            cls.listeners.clear()
