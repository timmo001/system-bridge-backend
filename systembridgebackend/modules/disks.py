"""Disks."""

import asyncio
from typing import override

from psutil import disk_io_counters, disk_partitions, disk_usage
from psutil._common import sdiskio, sdiskpart, sdiskusage

from systembridgemodels.modules.disks import (
    Disk,
    DiskIOCounters,
    DiskPartition,
    Disks,
    DiskUsage,
)

from .base import ModuleUpdateBase


class DisksUpdate(ModuleUpdateBase):
    """Disks Update."""

    async def _get_io_counters(self) -> sdiskio | None:
        """Disk IO counters."""
        return disk_io_counters()

    async def _get_io_counters_per_disk(self) -> dict[str, sdiskio]:
        """Disk IO counters per disk."""
        return disk_io_counters(perdisk=True)

    async def _get_partitions(self) -> list[sdiskpart]:
        """Disk partitions."""
        return disk_partitions(all=True)

    async def _get_usage(self, path: str) -> sdiskusage | None:
        """Disk usage."""
        try:
            return disk_usage(path)
        except (FileNotFoundError, PermissionError) as error:
            self._logger.warning(
                "Error getting disk usage for: %s",
                path,
                exc_info=error,
            )
            return None

    @override
    async def update_all_data(self) -> Disks:
        """Update all data."""
        self._logger.debug("Update all data")

        io_counters, io_counters_per_disk, partitions = await asyncio.gather(
            self._get_io_counters(),
            self._get_io_counters_per_disk(),
            self._get_partitions(),
        )

        devices: list[Disk] = []
        for partition in partitions:
            usage = await self._get_usage(partition.mountpoint)
            disk_partition = DiskPartition(
                device=partition.device,
                mount_point=partition.mountpoint,
                filesystem_type=partition.fstype,
                options=partition.opts,
                max_file_size=partition.maxfile,
                max_path_length=partition.maxpath,
                usage=DiskUsage(
                    free=usage.free,
                    total=usage.total,
                    used=usage.used,
                    percent=usage.percent,
                )
                if usage
                else None,
            )

            if partition.device not in devices:
                io_counters_item = io_counters_per_disk.get(partition.device)
                devices.append(
                    Disk(
                        name=partition.device,
                        partitions=[disk_partition],
                        io_counters=DiskIOCounters(
                            read_count=io_counters_item.read_count,
                            write_count=io_counters_item.write_count,
                            read_bytes=io_counters_item.read_bytes,
                            write_bytes=io_counters_item.write_bytes,
                            read_time=io_counters_item.read_time,
                            write_time=io_counters_item.write_time,
                        )
                        if io_counters_item
                        else None,
                    )
                )
            else:
                for device in devices:
                    if device.name == partition.device:
                        device.partitions.append(disk_partition)
                        break

        return Disks(
            devices=devices,
            io_counters=DiskIOCounters(
                read_count=io_counters.read_count,
                write_count=io_counters.write_count,
                read_bytes=io_counters.read_bytes,
                write_bytes=io_counters.write_bytes,
                read_time=io_counters.read_time,
                write_time=io_counters.write_time,
            )
            if io_counters
            else None,
        )
