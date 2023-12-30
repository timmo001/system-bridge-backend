"""Stoppable thread ."""
from asyncio import Event
from threading import Thread


class StoppableThread(Thread):
    """Thread class with a stop() method.

    The thread itself has to check regularly for the stopped() condition.
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the thread."""
        super().__init__(*args, **kwargs)
        self._stop_event = Event()

    def stop(self) -> None:
        """Stop the thread."""
        self._stop_event.set()

    def stopped(self) -> bool:
        """Return if the thread is stopped."""
        return self._stop_event.is_set()
