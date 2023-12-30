"""Data."""
from collections.abc import Awaitable, Callable
from typing import Any

from systembridgemodels.modules import ModulesData
from systembridgeshared.base import Base

from ..threads.media import UpdateMediaThread
from ..threads.update import UpdateThread


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
