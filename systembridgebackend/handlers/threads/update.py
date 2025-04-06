"""Update thread handler."""

import asyncio
from datetime import datetime, timedelta
from queue import Queue, Empty
import threading
import time
from typing import override

from . import BaseThread


class UpdateThread(BaseThread):
    """Update thread."""

    def __init__(
        self,
        interval: int,
        update_queue: Queue[dict],
    ) -> None:
        """Initialise."""
        super().__init__()
        self.interval = interval
        self.next_run: datetime = datetime.now()
        self._thread: threading.Thread | None = None
        self.update_queue = update_queue

    @override
    def run(self) -> None:
        """
        Run update loop. Trigger update on interval or when a signal from `update_queue` is received.
        """
        try:
            while not self.stopping:
                update_triggered_by_signal = False
                update_params = {}

                # Wait for the next run
                if (sleep_time := (self.next_run - datetime.now()).total_seconds()) > 0:
                    self._logger.info("Waiting for next update in %.2f seconds", sleep_time)
                    try:
                        update_params = self.update_queue.get(block=True, timeout=sleep_time)
                        self._logger.debug("Update triggered by force update, with params: %s", update_params)
                        # Update is triggered by signal from another thread
                        update_triggered_by_signal = True
                    except Empty:
                        self._logger.debug("Update triggered by time interval")

                if self.stopping:
                    return

                if not update_triggered_by_signal:
                    # Update the next run before running the update
                    self.update_next_run()

                # Run the update
                try:
                    asyncio.new_event_loop().run_until_complete(self.update(**update_params))
                except Exception as exception:  # pylint: disable=broad-except
                    self._logger.exception(exception)

                if self.stopping:
                    return

                self._logger.info("Update finished, next run will be at: %s", self.next_run)
        finally:
            self._logger.info("%s Stopped", self.__class__.__name__)

    def _update_interval(
        self,
        interval: int,
    ) -> None:
        """Update the interval if it has changed."""
        if self.interval == interval:
            return

        self.interval = interval
        self._logger.info("Updated update interval to: %s", self.interval)

    async def update(self) -> None:
        """The actual data/media update function, should be implemented in subclasses."""
        raise NotImplementedError

    def update_next_run(self) -> None:
        """Update `self.next_run` to be the current time plus the update interval."""
        if self.stopping:
            return
        self.next_run = datetime.now() + timedelta(seconds=self.interval)
        self._logger.info("Scheduled next update for: %s", self.next_run)
