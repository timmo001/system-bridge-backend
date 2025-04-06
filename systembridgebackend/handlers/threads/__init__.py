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

    def interrupt(
        self,
        timeout: float | None = None,
    ) -> None:
        """
        Interrupt thread running by setting the `self.stopping` flag.
        Child classes should check `self.stopping` in its `run()` implementation
        to support this feature.

        Should be called instead of `BaseThread.join()`.
        """
        self._logger.info("Interrupting %s", self.__class__.__name__)
        self.stopping = True
        loop = asyncio.get_event_loop()
        asyncio.tasks.all_tasks(loop).clear()
        loop.stop()
        super().join(timeout)
