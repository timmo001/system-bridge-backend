"""Media thread handler."""
import asyncio
from collections.abc import Awaitable, Callable
import platform

from systembridgemodels.modules.media import Media as MediaInfo

from ..modules.media import Media
from . import BaseThread


class UpdateMediaThread(BaseThread):
    """Update media thread."""

    def __init__(
        self,
        updated_callback: Callable[[str, MediaInfo], Awaitable[None]],
    ) -> None:
        """Initialise."""
        super().__init__()

        if platform.system() != "Windows":
            return

        self._media = Media(updated_callback)

    def run(self) -> None:
        """Run."""
        if platform.system() != "Windows":
            return

        try:
            asyncio.run(self._media.update_media_info())
        except Exception as exception:  # pylint: disable=broad-except
            self._logger.exception(exception)
