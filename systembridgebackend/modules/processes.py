"""Processes"""
from __future__ import annotations

from typing import override

from psutil import AccessDenied, NoSuchProcess, process_iter
from systembridgemodels.processes import Process, Processes

from .._version import __version__
from .base import ModuleUpdateBase


class ProcessesUpdate(ModuleUpdateBase):
    """Processes Update"""

    @override
    async def update_all_data(self) -> Processes:
        """Update all data"""
        self._logger.debug("Update all data")

        process_list = list(process_iter())

        # Get names of processes
        items = []
        for process in process_list:
            model = Process(id=process.pid)

            try:
                model.name = process.name()
                model.cpu_usage = process.cpu_percent()
                model.created = process.create_time()
                model.memory_usage = process.memory_percent()
                model.path = process.exe()
                model.status = process.status()
                model.username = process.username()
            except (AccessDenied, NoSuchProcess, OSError) as error:
                self._logger.debug(
                    "Failed to get process information for PID %s",
                    process.pid,
                    exc_info=error,
                )
            items.append(model)
        # Sort by name
        items = sorted(items, key=lambda item: item.name or "")

        return items
