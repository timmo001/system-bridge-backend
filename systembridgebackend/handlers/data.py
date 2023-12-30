"""Data."""
from collections.abc import Awaitable, Callable
from typing import Any

from systembridgemodels.modules import ModulesData
from systembridgeshared.base import Base

from .threads.data import DataUpdateThread
from .threads.media import MediaUpdateThread


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
        self.update_thread: DataUpdateThread | None = None
        self.update_media_thread: MediaUpdateThread | None = None

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
        if self.update_thread is not None and self.update_thread.is_alive():
            self._logger.info("Update thread already running")
            return

        self._logger.info("Starting update thread")
        self.update_thread = DataUpdateThread(self._data_updated_callback)
        self.update_thread.start()

    def request_update_media_data(self) -> None:
        """Request update media data."""
        if self.update_media_thread is not None and self.update_media_thread.is_alive():
            self._logger.info("Update media thread already running")
            return

        self._logger.info("Starting update media thread")
        self.update_media_thread = MediaUpdateThread(self._data_updated_callback)
        self.update_media_thread.start()
