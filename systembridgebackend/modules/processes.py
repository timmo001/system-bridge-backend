"""System Bridge: Processes"""
from __future__ import annotations

import asyncio
from json import dumps

from psutil import AccessDenied, NoSuchProcess, Process, process_iter
from systembridgemodels.processes import Process as ProcessModel
from systembridgeshared.models.database_data import Processes as DatabaseModel

from .._version import __version__
from .base import ModuleUpdateBase


class ProcessesUpdate(ModuleUpdateBase):
    """Processes Update"""

    async def update_count(
        self,
        processes: list[Process],
    ) -> None:
        """Update count"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="count",
                value=str(len(list(processes))),
            ),
        )

    async def update_processes(
        self,
        processes: list[Process],
    ) -> None:
        """Update processes"""
        # Get names of processes
        items = []
        for process in processes:
            try:
                items.append(
                    ProcessModel(
                        id=process.pid,
                        name=process.name(),
                        cpu_usage=process.cpu_percent(),
                        created=process.create_time(),
                        memory_usage=process.memory_percent(),
                        path=process.exe(),
                        status=process.status(),
                        username=process.username(),
                        working_directory=process.cwd(),
                    )
                )
            except (AccessDenied, NoSuchProcess, OSError):
                continue
        # Update data
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="processes",
                value=dumps([item.dict(exclude_none=True) for item in items]),
            ),
        )

    async def update_all_data(self) -> None:
        """Update data"""
        processes = list(process_iter())
        await asyncio.gather(
            *[
                self.update_count(processes),
                self.update_processes(processes),
            ]
        )
