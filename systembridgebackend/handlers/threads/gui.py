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
        failed_callback: Callable[[], None] | None = None,
        attempt: int = 1,
        command: str = "main",
    ) -> None:
        """Start the GUI."""
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
                    self._logger.error("GUI exited with code: %s", exit_code)
                    await self._start(
                        *args,
                        failed_callback=failed_callback,
                        attempt=attempt + 1,
                        command=command,
                    )
                    return
            self._logger.info("GUI exited with code: %s", exit_code)

    def _start_gui_sync(  # pylint: disable=keyword-arg-before-vararg
        self,
        *args,
        failed_callback: Callable[[], None] | None = None,
        command: str = "main",
    ) -> None:
        """Start the GUI in a synchronous thread."""
        asyncio.run(
            self._start(
                *args,
                failed_callback=failed_callback,
                attempt=1,
                command=command,
            )
        )

    @override
    def run(
        self,
        *args,
        failed_callback: Callable[[], None] | None = None,
        command: str = "main",
    ) -> None:
        """Run the thread."""
        self._start_gui_sync(
            *args,
            failed_callback=failed_callback,
            command=command,
        )
