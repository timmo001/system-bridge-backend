"""Data."""

from collections.abc import Awaitable, Callable
from queue import Queue
from typing import Any

from systembridgemodels.modules import ModulesData
from systembridgeshared.base import Base

from .threads.data import DataUpdateThread
from .threads.media import MediaUpdateThread


class DataUpdate(Base):
    """
    The update threads scheduler, managing data update thread and media update thread.
    Also holds a reference to the collected data.
    """

    def __init__(
        self,
        updated_callback: Callable[[str], Awaitable[None]]
    ) -> None:
        """
        Initialize a new instance of DataUpdate.

        :param updated_callback: The callback to be invoked when data is updated.
        """
        super().__init__()
        self._updated_callback = updated_callback
        self.update_data_thread: DataUpdateThread | None = None
        self.update_media_thread: MediaUpdateThread | None = None
        self.update_data_queue: Queue[dict] = Queue()
        self.update_media_queue: Queue[dict] = Queue()

        self.data = ModulesData()
        """Data collected by the system bridge"""

    async def _data_updated_callback(
        self,
        name: str,
        data: Any,
    ) -> None:
        """
        Update collected data of given module, then invoke :field:`_updated_callback`.

        :param name: module name triggering the update. should be any field names of :class:`ModulesData`.
        :param data: The dataclass object to be assigned to given module.
        """
        setattr(self.data, name, data)
        await self._updated_callback(name)

    def request_update_data(self, **kwargs) -> None:
        """
        Trigger data update by enqueueing `kwargs` to :field:`update_data_queue`,
        these args will be passed to `DataUpdateThread.update`,
        and then to `ModulesUpdate.update_data`.

        will start :field:`update_data_thread` if necessary.

        :param kwargs: The parameters to be passed into `ModulesUpdate.update_data`.
        """

        if self.update_data_thread is not None and self.update_data_thread.is_alive():
            self._logger.warning("Force update data with params: %s", kwargs)
            self.update_data_queue.put_nowait(kwargs)
            return

        self._logger.info("Starting update data thread..")
        self.update_data_thread = DataUpdateThread(self._data_updated_callback, self.update_data_queue)
        self.update_data_thread.start()
        if kwargs:
            self.update_data_queue.put_nowait(kwargs)

    def request_update_media_data(self) -> None:
        """
        Trigger media update by enqueueing `kwargs` to :field:`update_media_queue`,
        these args will be passed to `MediaUpdateThread.update`,
        and then to `Media.update_media_info`.

        will start :field:`update_media_thread` if necessary.

        :param kwargs: The parameters to be passed into `Media.update_media_info`.
        """
        if self.update_media_thread is not None and self.update_media_thread.is_alive():
            self._logger.info("Update media thread already running")
            return

        self._logger.info("Starting update media thread..")
        self.update_media_thread = MediaUpdateThread(self._data_updated_callback, self.update_media_queue)
        self.update_media_thread.start()
