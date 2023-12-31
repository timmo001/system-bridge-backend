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
        *args,
        **kwargs,
    ) -> None:
        """Initialise the thread."""
        super().__init__(*args, **kwargs)
        self._process: subprocess.Popen | None = None

    async def _start(
        self,
        *args,
        attempt: int = 1,
        command: str = "main",
        failed_callback: Callable[[], None] | None = None,
    ) -> None:
        """Start the GUI."""
        if self.stopping:
            self._logger.warning("Thread is stopping, cannot start GUI")
            return

        if attempt > 2:
            self._logger.error("Failed to start GUI after 2 attempts")
            if failed_callback is not None:
                failed_callback()
            return

        pgm_args = (
            [
                sys.executable,
                "-m",
                "systembridgegui",
                command,
                *args,
            ]
            if "python" in sys.executable
            else [
                sys.executable,
                "gui",
                command,
                *args,
            ]
        )

        self._logger.info("Starting GUI: %s", pgm_args)
        with subprocess.Popen(pgm_args) as self._process:
            self._logger.info("GUI started with PID: %s", self._process.pid)
            if (exit_code := self._process.wait()) != 0:
                if not self.stopping:
                    self._logger.error("GUI exited abnormally with code: %s", exit_code)
                    await self._start(
                        *args,
                        failed_callback=failed_callback,
                        attempt=attempt + 1,
                        command=command,
                    )
                    return
            self._logger.info("GUI exited normally with code: %s", exit_code)

    @override
    def run(
        self,
        *args,
        command: str = "main",
        failed_callback: Callable[[], None] | None = None,
    ) -> None:
        """Run the thread."""
        if self.stopping:
            self._logger.warning("Thread is stopping, cannot start GUI")
            return

        asyncio.run(
            self._start(
                *args,
                attempt=1,
                command=command,
                failed_callback=failed_callback,
            )
        )

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
