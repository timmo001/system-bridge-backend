"""System Bridge: Processes"""
from __future__ import annotations

import asyncio
from collections.abc import Iterator
from json import dumps

from psutil import Process, process_iter
from systembridgeshared.models.database_data import Processes as DatabaseModel

from .._version import __version__
from .base import ModuleUpdateBase


class ProcessesUpdate(ModuleUpdateBase):
    """Processes Update"""

    async def update_count(
        self,
        processes: Iterator[Process],
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
        processes: Iterator[Process],
    ) -> None:
        """Update processes"""
        names: list[str] = [process.name() for process in processes]
        names_sorted: list[str] = sorted(names, key=str.casefold)
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="processes",
                value=dumps(names_sorted),
            ),
        )

    async def update_all_data(self) -> None:
        """Update data"""
        processes = process_iter()
        await asyncio.gather(
            *[
                self.update_count(processes),
                self.update_processes(processes),
            ]
        )
