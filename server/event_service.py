"""Event service for handling events between services"""

import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class EventService:
    """Moves events between services and handles event processing.

    Instance-level state means each EventService is isolated —
    no shared mutable class variables that leak across tests.
    """

    def __init__(self) -> None:
        self._listeners: Dict[str, List[Callable]] = {}

    def add_listener(self, event_name: str, callback: Callable) -> None:
        """Add a listener for an event"""
        logger.debug("Adding listener for event: %s", event_name)
        self._listeners.setdefault(event_name, []).append(callback)

    async def emit(self, event_name: str, data: Any) -> None:
        """Emit an event to all listeners"""
        logger.info("Emitting event: %s", event_name)
        logger.debug("Event data: %s", data)
        for callback in self._listeners.get(event_name, []):
            try:
                await callback(data)
            except Exception as e:
                logger.error(
                    "Error in event listener for %s: %s", event_name, e, exc_info=True
                )

    def clear_listeners(self, event_name: str | None = None) -> None:
        """Clear listeners for a specific event or all events"""
        if event_name:
            self._listeners.pop(event_name, None)
        else:
            self._listeners.clear()
