"""Data."""
import asyncio
from collections.abc import Awaitable, Callable
import platform
from threading import Thread
from typing import Any

from systembridgemodels.data import Data
from systembridgemodels.media import Media as MediaInfo
from systembridgeshared.base import Base

from .modules import Update


class UpdateThread(Thread):
    """Update thread."""

    def __init__(
        self,
        updated_callback: Callable[[str, Any], Awaitable[None]],
    ) -> None:
        """Initialise."""
        super().__init__()
        self._update = Update(updated_callback)

    def run(self) -> None:
        """Run."""
        asyncio.run(self._update.update_data())


    def join(self, timeout: float | None = None) -> None:
        """Join."""
        loop = asyncio.get_event_loop()
        asyncio.tasks.all_tasks(loop).clear()
        loop.stop()
        super().join(timeout)

class UpdateMediaThread(Thread):
    """Update media thread."""

    def __init__(
        self,
        updated_callback: Callable[[str, MediaInfo], Awaitable[None]],
    ) -> None:
        """Initialise."""
        super().__init__()

        if platform.system() != "Windows":
            return

        from .modules.media import (  # pylint: disable=import-error, import-outside-toplevel
            Media,
        )

        self._media = Media(updated_callback)

    def run(self) -> None:
        """Run."""
        if platform.system() != "Windows":
            return

        asyncio.run(self._media.update_media_info())


    def join(self, timeout: float | None = None) -> None:
        """Join."""
        loop = asyncio.get_event_loop()
        asyncio.tasks.all_tasks(loop).clear()
        loop.stop()
        super().join(timeout)

class DataUpdate(Base):
    """Data Update."""

    def __init__(
        self,
        updated_callback: Callable[[str], Awaitable[None]],
    ) -> None:
        """Initialise."""
        super().__init__()
        self.data = Data()
        self._updated_callback = updated_callback
        self.update_thread = UpdateThread(self._data_updated_callback)
        self.update_media_thread = UpdateMediaThread(self._data_updated_callback)

    async def _data_updated_callback(
        self,
        name: str,
        data: Any,
    ) -> None:
        """Data updated callback."""
        setattr(self.data, name, data)
        await self._updated_callback(name)

    def request_update_data(self) -> None:
        """Request update data."""
        if self.update_thread.is_alive():
            self._logger.warning("Update thread is already alive")
            return
        self.update_thread.start()

    def request_update_media_data(self) -> None:
        """Request update media data."""
        if self.update_media_thread.is_alive():
            self._logger.warning("Update media thread is already alive")
            return
        self.update_media_thread.start()
