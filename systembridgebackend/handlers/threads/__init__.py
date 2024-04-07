"""Thread handlers."""

import asyncio
from threading import Thread

from systembridgeshared.base import Base


class BaseThread(Thread, Base):
    """Base thread."""

    def __init__(
        self,
        *args,
        **kwargs,
    ) -> None:
        """Initialise."""
        Thread.__init__(self, *args, **kwargs)
        Base.__init__(self)
        self.stopping = False

    def run(self) -> None:
        """Run."""
        raise NotImplementedError

    def join(
        self,
        timeout: float | None = None,
    ) -> None:
        """Join."""
        self._logger.info("Stopping thread")
        self.stopping = True
        loop = asyncio.get_event_loop()
        asyncio.tasks.all_tasks(loop).clear()
        loop.stop()
        super().join(timeout)
