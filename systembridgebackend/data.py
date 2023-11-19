"""System Bridge: Data"""
import asyncio
from collections.abc import Awaitable, Callable
from threading import Thread
from typing import Any

from systembridgemodels.data import Data
from systembridgeshared.base import Base

from .modules import Update


class UpdateThread(Thread):
    """Update thread"""

    def __init__(
        self,
        updated_callback: Callable[[str, Any], Awaitable[None]],
    ) -> None:
        """Initialise"""
        super().__init__()
        self._update = Update(updated_callback)

    def run(self) -> None:
        """Run"""
        asyncio.run(self._update.update_data())


# class UpdateEventsThread(Thread):
#     """Update events thread"""

#     def __init__(
#         self,
#         updated_callback: Callable[[str, Any], Awaitable[None]],
#     ) -> None:
#         """Initialise"""
#         super().__init__()

#         if platform.system() != "Windows":
#             return

#         from .modules.media import (  # pylint: disable=import-error, import-outside-toplevel
#             Media,
#         )

#         self._media = Media(updated_callback)

#     def run(self) -> None:
#         """Run"""
#         if platform.system() != "Windows":
#             return

#         asyncio.run(self._media.update_media_info())


class DataUpdate(Base):
    """Data Update"""

    def __init__(
        self,
        updated_callback: Callable[[str], Awaitable[None]],
    ) -> None:
        """Initialise"""
        super().__init__()
        self.data = Data()
        self._updated_callback = updated_callback

    async def _data_updated_callback(
        self,
        name: str,
        data: Any,
    ) -> None:
        """Data updated callback"""
        setattr(self.data, name, data)
        await self._updated_callback(name)

    def request_update_data(self) -> None:
        """Request update data"""
        thread = UpdateThread(self._data_updated_callback)
        thread.start()

    # def request_update_events_data(self) -> None:
    #     """Request update events data"""
    #     thread = UpdateEventsThread(self._updated_callback)
    #     thread.start()
