"""System Bridge: Disk"""
from __future__ import annotations

import asyncio
from json import dumps
from typing import NamedTuple, Optional

from psutil import disk_io_counters, disk_partitions, disk_usage
from psutil._common import sdiskio, sdiskpart
from systembridgeshared.base import Base
from systembridgeshared.database import Database
from systembridgeshared.models.database_data import Disk as DatabaseModel

from .base import ModuleUpdateBase


class Disk(Base):
    """Disk"""

    def io_counters(self) -> Optional[sdiskio]:
        """Disk IO counters"""
        return disk_io_counters()

    def io_counters_per_disk(self) -> dict[str, sdiskio]:
        """Disk IO counters per disk"""
        return disk_io_counters(perdisk=True)

    def partitions(self) -> list[sdiskpart]:
        """Disk partitions"""
        return disk_partitions(all=True)

    def usage(self, path: str) -> Optional[NamedTuple]:
        """Disk usage"""
        try:
            return disk_usage(path)
        except PermissionError as error:
            self._logger.error("PermissionError: %s", error)
            return None


class DiskUpdate(ModuleUpdateBase):
    """Disk Update"""

    def __init__(
        self,
        database: Database,
    ) -> None:
        """Initialize"""
        super().__init__(database)
        self._disk = Disk()

    async def update_io_counters(self) -> None:
        """Update IO counters"""
        if io_counters := self._disk.io_counters():
            for key, value in io_counters._asdict().items():
                self._database.update_data(
                    DatabaseModel,
                    DatabaseModel(
                        key=f"io_counters_{key}",
                        value=value,
                    ),
                )

    async def update_io_counters_per_disk(self) -> None:
        """Update IO counters per disk"""
        for key, value in self._disk.io_counters_per_disk().items():  # type: ignore
            for subkey, subvalue in value._asdict().items():
                self._database.update_data(
                    DatabaseModel,
                    DatabaseModel(
                        key=f"io_counters_per_disk_{key}_{subkey}",
                        value=subvalue,
                    ),
                )

    async def update_partitions(self) -> None:
        """Update partitions"""
        device_list = []
        partition_list = []
        for partition in self._disk.partitions():
            if partition.device not in device_list:
                device_list.append(partition.device)
            partition_list.append(partition.mountpoint)
            for key, value in partition._asdict().items():
                self._database.update_data(
                    DatabaseModel,
                    DatabaseModel(
                        key=f"partitions_{partition.mountpoint}_{key}",
                        value=value,
                    ),
                )
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="devices",
                value=dumps(device_list),
            ),
        )
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="partitions",
                value=dumps(partition_list),
            ),
        )

    async def update_usage(self) -> None:
        """Update usage"""
        for partition in self._disk.partitions():
            if data := self._disk.usage(partition.mountpoint):
                for key, value in data._asdict().items():
                    self._database.update_data(
                        DatabaseModel,
                        DatabaseModel(
                            key=f"usage_{partition.mountpoint}_{key}",
                            value=value,
                        ),
                    )

    async def update_all_data(self) -> None:
        """Update data"""
        await asyncio.gather(
            *[
                self.update_io_counters(),
                self.update_io_counters_per_disk(),
                self.update_partitions(),
                self.update_usage(),
            ]
        )
