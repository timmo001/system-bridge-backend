"""Data."""
import asyncio
from collections.abc import Awaitable, Callable
import platform
from threading import Thread
from typing import Any

from systembridgemodels.modules import ModulesData
from systembridgemodels.modules.media import Media as MediaInfo
from systembridgeshared.base import Base

from .modules import Update


class UpdateThread(Thread, Base):
    """Update thread."""

    def __init__(
        self,
        updated_callback: Callable[[str, Any], Awaitable[None]],
    ) -> None:
        """Initialise."""
        Thread.__init__(self)
        Base.__init__(self)
        self._update = Update(updated_callback)

    def run(self) -> None:
        """Run."""
        try:
            asyncio.run(self._update.update_data())
        except Exception as exception:  # pylint: disable=broad-except
            self._logger.exception(exception)

    def join(self, timeout: float | None = None) -> None:
        """Join."""
        loop = asyncio.get_event_loop()
        asyncio.tasks.all_tasks(loop).clear()
        loop.stop()
        super().join(timeout)


# pylint: disable=import-error, import-outside-toplevel
class UpdateMediaThread(Thread, Base):
    """Update media thread."""

    def __init__(
        self,
        updated_callback: Callable[[str, MediaInfo], Awaitable[None]],
    ) -> None:
        """Initialise."""
        super().__init__()

        if platform.system() != "Windows":
            return

        from .modules.media import Media

        self._media = Media(updated_callback)

    def run(self) -> None:
        """Run."""
        if platform.system() != "Windows":
            return

        try:
            asyncio.run(self._media.update_media_info())
        except Exception as exception:  # pylint: disable=broad-except
            self._logger.exception(exception)

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
        self.data = ModulesData()
        self._updated_callback = updated_callback
        self.update_thread: UpdateThread | None = None
        self.update_media_thread: UpdateMediaThread | None = None

    async def _data_updated_callback(
        self,
        name: str,
        data: Any,
    ) -> None:
        """Update the data with the given name and value and invoke the updated callback."""
        setattr(self.data, name, data)
        await self._updated_callback(name)

    def request_update_data(self) -> None:
        """Request update data."""
        self.update_thread = UpdateThread(self._data_updated_callback)
        self.update_thread.start()

    def request_update_media_data(self) -> None:
        """Request update media data."""
        self.update_media_thread = UpdateMediaThread(self._data_updated_callback)
        self.update_media_thread.start()
