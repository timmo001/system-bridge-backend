"""GUI handler."""
import asyncio
from collections.abc import Callable
import subprocess
import sys

from systembridgeshared.base import Base
from systembridgeshared.settings import Settings

from .threads.stoppable import StoppableThread


class GUI(Base):
    """GUI."""

    def __init__(
        self,
        settings: Settings,
    ):
        """Initialise."""
        super().__init__()
        self._settings = settings

        self._name = "GUI"
        self._process: subprocess.Popen | None = None
        self._stopping = False
        self._thread: StoppableThread | None = None

    async def _start(  # pylint: disable=keyword-arg-before-vararg
        self,
        failed_callback: Callable[[], None] | None,
        attempt: int = 1,
        command: str | None = None,
        *args,
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

        self._name = command

        self._logger.info("Starting GUI: %s", pgm_args)
        with subprocess.Popen(pgm_args) as self._process:
            self._logger.info("GUI started with PID: %s", self._process.pid)
            if (exit_code := self._process.wait()) != 0:
                if not self._stopping:
                    self._logger.error("GUI exited with code: %s", exit_code)
                    await self._start(
                        failed_callback,
                        attempt + 1,
                        command,
                        *args,
                    )
                    return
            self._logger.info("GUI exited with code: %s", exit_code)

    def _start_gui_sync(  # pylint: disable=keyword-arg-before-vararg
        self,
        failed_callback: Callable[[], None] | None,
        command: str = "main",
        *args,
    ) -> None:
        """Start the GUI in a synchronous thread."""
        asyncio.run(
            self._start(
                failed_callback,
                1,
                command,
                *args,
            )
        )

    async def start(  # pylint: disable=keyword-arg-before-vararg
        self,
        failed_callback: Callable[[], None] | None,
        command: str = "main",
        *args,
    ) -> None:
        """Start the GUI."""
        self._thread = StoppableThread(
            target=self._start_gui_sync,
            args=(
                failed_callback,
                command,
                *args,
            ),
        )
        self._thread.start()
        self._stopping = False

    def stop(self) -> None:
        """Stop the GUI."""
        self._logger.info("Stopping GUI: %s", self._name)
        self._stopping = True
        if self._process is not None:
            self._process.terminate()
            self._process.wait()
            self._process = None
            self._logger.info("GUI stopped")
        if self._thread is not None:
            self._thread.stop()
