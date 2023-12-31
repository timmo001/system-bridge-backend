"""GUI handler."""
from collections.abc import Callable
from enum import Enum

from systembridgeshared.base import Base
from systembridgeshared.settings import Settings

from .threads.gui import GUIThread


class GUICommand(Enum):
    """GUI commands."""

    MAIN = "main"
    NOTIFICATION = "notification"
    PLAYER = "player"


class GUI(Base):
    """GUI."""

    def __init__(
        self,
        settings: Settings,
    ):
        """Initialise."""
        super().__init__()
        self._settings = settings
        self._name = ""
        self._thread: GUIThread | None = None

    async def start(
        self,
        *args,
        failed_callback: Callable[[], None] | None = None,
        command: GUICommand = GUICommand.MAIN,
    ) -> None:
        """Start the GUI."""
        if self._thread is not None:
            self._logger.warning(
                "GUI thread already running for %s, cannot start", self._name
            )
            return

        self._logger.info("Starting GUI thread: %s", command)
        self._name = command.value
        self._thread = GUIThread(
            args=(
                *args,
                failed_callback,
                command,
            ),
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the GUI."""
        # Stop the thread if it is running
        if self._thread is None or not self._thread.is_alive():
            self._logger.warning("GUI thread not running, cannot stop")
            return

        self._logger.info("Stopping GUI thread: %s", self._name)
        # Stop the GUI thread
        self._thread.join(timeout=5)
