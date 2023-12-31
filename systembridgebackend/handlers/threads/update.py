"""Update thread handler."""
import asyncio
from datetime import datetime, timedelta
import threading
import time
from typing import override

from . import BaseThread


class UpdateThread(BaseThread):
    """Update thread."""

    def __init__(
        self,
        interval: int,
    ) -> None:
        """Initialise."""
        super().__init__()
        self.interval = interval
        self.next_run: datetime | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _run(self) -> None:
        """Private method to automatically update the schedule."""
        while not self._stop.is_set():
            # Update the next run before running the update
            self.update_next_run()

            # Run the update
            try:
                asyncio.new_event_loop().run_until_complete(self.update())
            except Exception as exception:  # pylint: disable=broad-except
                self._logger.exception(exception)

            self._logger.info(
                "Update finished, waiting for next run at: %s", self.next_run
            )

            # Wait for the next run
            time.sleep(self.interval)

    def _update_interval(
        self,
        interval: int,
    ) -> None:
        """Update the interval if it has changed."""
        if self.interval == interval:
            return

        self.interval = interval
        self._logger.info("Updated update interval to: %s", self.interval)

    @override
    def run(
        self,
        *_,
    ) -> None:
        """Run."""
        # Start the automatic update in a separate thread
        self._thread = threading.Thread(target=self._run)
        self._thread.start()
        self._logger.info("Started update thread")

    def update_next_run(self) -> None:
        """Update next run."""
        # Update the next run time to be the current time plus the interval
        self.next_run = datetime.now() + timedelta(seconds=self.interval)
        self._logger.info("Scheduled next update for: %s", self.next_run)

    def stop(self) -> None:
        """Stop the automatic update."""
        # Stop the automatic update thread if it is running
        if self._thread and self._thread.is_alive():
            self._stop.set()
            self._thread.join(timeout=4)
            self._logger.info("Stopped update thread")

    async def update(self) -> None:
        """Update."""
        raise NotImplementedError
