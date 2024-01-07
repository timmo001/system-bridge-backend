"""GUI thread handler."""
import asyncio
from collections.abc import Callable
import subprocess
import sys
from typing import override

from . import BaseThread


class GUIThread(BaseThread):
    """GUI thread."""

    def __init__(
        self,
        command: str = "main",
        data: str | None = None,
        failed_callback: Callable[[], None] | None = None,
    ) -> None:
        """Initialise the thread."""
        super().__init__()
        self._process: subprocess.Popen | None = None
        self._command = command
        self._data = data
        self._failed_callback = failed_callback

    async def _start(
        self,
        attempt: int = 1,
    ) -> None:
        """Start the GUI."""
        if self.stopping:
            self._logger.warning("Thread is stopping, cannot start GUI")
            return

        if attempt > 2:
            self._logger.error("Failed to start GUI after 2 attempts")
            if self._failed_callback is not None:
                self._failed_callback()
            return

        pgm_args = (
            [
                sys.executable,
                "-m",
                "systembridgegui",
                self._command,
            ]
            if "python" in sys.executable
            else [
                sys.executable,
                "gui",
                self._command,
            ]
        )

        # Add data if it is not None
        if self._data is not None:
            pgm_args.append(self._data)

        self._logger.info("Starting GUI: %s", pgm_args)
        with subprocess.Popen(pgm_args) as self._process:
            self._logger.info("GUI started with PID: %s", self._process.pid)
            if (exit_code := self._process.wait()) != 0:
                if not self.stopping:
                    self._logger.error("GUI exited abnormally with code: %s", exit_code)
                    await self._start(attempt=attempt + 1)
                    return
            self._logger.info("GUI exited normally with code: %s", exit_code)

    @override
    def run(self) -> None:
        """Run the thread."""
        if self.stopping:
            self._logger.warning("Thread is stopping, cannot start GUI")
            return

        asyncio.run(self._start(attempt=1))

        self.stopping = True

    @override
    def join(
        self,
        timeout: float | None = None,
    ) -> None:
        """Join."""
        self.stopping = True

        # Stop the GUI process if it is running
        if self._process is not None:
            self._logger.info("Stopping GUI process")
            self._process.terminate()

        super().join(timeout)
