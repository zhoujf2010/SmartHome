"""
通用的事件总线
"""
from __future__ import annotations
from typing import Any, Callable
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)


class EventBus():
    def __init__(self) -> None:
        self.loop = asyncio.get_running_loop()
        self._listeners: dict[str, list[Callable]] = {}

    def async_listen(
        self,
        event_type: str,
        listener: Callable
    ) -> Callable[[], None]:
        """Listen for all events or events of a specific type.

        To listen to all events specify the constant ``MATCH_ALL``
        as event_type.

        An optional event_filter, which must be a callable decorated with
        @callback that returns a boolean value, determines if the
        listener callable should run.

        This method must be run in the event loop.
        """
        self._listeners.setdefault(event_type, []).append(listener)

        def remove_listener() -> None:
            """Remove the listener."""
            try:
                self._listeners[event_type].remove(listener)

                # delete event_type list if empty
                if not self._listeners[event_type]:
                    self._listeners.pop(event_type)
            except (KeyError, ValueError):
                # KeyError is key event_type listener did not exist
                # ValueError if listener did not exist within event_type
                _LOGGER.exception(
                    "Unable to remove unknown job listener %s", listener
                )

        return remove_listener

    def async_fire(self, event_type: str, event_data: Any | None = None) -> None:
        """Fire an event.

        This method must be run in the event loop.
        """
        listeners = self._listeners.get(event_type, [])

        if not listeners:
            return

        for job in listeners:
            self.loop.run_in_executor(None, job, event_type, event_data)
