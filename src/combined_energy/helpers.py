"""Helpers for using the API client."""

from collections import deque
from datetime import datetime, timedelta
import logging
from typing import AsyncIterator

from .client import CombinedEnergy
from .models import Readings

LOGGER = logging.getLogger(__package__)

now = datetime.now


class ReadingsIterator:
    """Iterator that returns readings with a certain interval specified."""

    __slots__ = ("client", "increment", "initial_delta", "_last_end", "_empty")

    def __init__(
        self,
        client: CombinedEnergy,
        *,
        increment: int,
        initial_delta: timedelta = None,
        log_session_reset_count: int = 3,
    ):
        """Initialise iterator."""
        self.client = client
        self.increment = increment
        self.initial_delta = initial_delta

        self._last_end: datetime | None = None
        # Prefill with False
        self._empty = deque([False] * log_session_reset_count, log_session_reset_count)

    @property
    def next_range_start(self) -> datetime | None:
        """Calculate the next range start value."""
        if self._last_end:
            return self._last_end
        if self.initial_delta:
            return now() - self.initial_delta

    async def _check_for_log_session_restart(self) -> None:
        """Check if a start log session message is required.

        This is a strange behaviour of this API that requires the client to
        call start new log session. In the dashboard app this is covered up
        with a dialog that pops up periodically.
        """
        # Reset if deque is full of True statuses
        if all(self._empty):
            LOGGER.info("Log session expired, restarting...")
            await self.client.start_log_session()

    async def __anext__(self) -> Readings:
        """Async Next implementation."""
        await self._check_for_log_session_restart()

        readings = await self.client.readings(
            self.next_range_start, None, self.increment
        )

        # Update state
        self._empty.append(readings.range_count == 0)
        self._last_end = readings.range_end

        return readings

    async def __aiter__(self) -> AsyncIterator[Readings]:
        """Async iterator implementation."""

        # Start log session up front if required
        await self.client.start_log_session()

        while True:
            yield await self.__anext__()
