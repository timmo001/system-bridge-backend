"""Update thread handler."""
import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
import threading
import time
from typing import Any

from ...modules import Update
from . import BaseThread


class UpdateThread(BaseThread):
    """Update thread."""

    def __init__(
        self,
        interval: int,
        updated_callback: Callable[[str, Any], Awaitable[None]],
    ) -> None:
        """Initialise."""
        super().__init__()
        self._update = Update(updated_callback)
        self.interval = interval
        self.next_run: datetime | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def _run(self):
        """Private method to automatically update the schedule."""
        while not self._stop.is_set():
            # Update the next run before running the update
            self.update_next_run()

            # Run the update
            try:
                asyncio.run(self._update.update_data())
                self._logger.info("Update successful")
            except asyncio.CancelledError as exception:
                self._logger.exception(exception)

            # Wait for the next run
            time.sleep(self.interval)

    def run(self) -> None:
        """Run."""
        # Start the automatic update in a separate thread
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def get_next_run(self):
        """Get next run."""
        return self.next_run

    def update_next_run(self):
        """Update next run."""
        # Update the next run time to be the current time plus the interval
        self.next_run = datetime.now() + timedelta(seconds=self.interval)

    def stop(self):
        """Stop the automatic update."""
        # Stop the automatic update thread if it is running
        if self._thread and self._thread.is_alive():
            self._stop.set()
            self._thread.join()
