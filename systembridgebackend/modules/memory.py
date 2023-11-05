"""System Bridge: Memory"""
import asyncio
from typing import NamedTuple

from psutil import swap_memory, virtual_memory
from psutil._common import sswap
from systembridgeshared.base import Base
from systembridgeshared.database import Database
from systembridgeshared.models.database_data import Memory as DatabaseModel

from .base import ModuleUpdateBase


class Memory(Base):
    """Memory"""

    def swap(self) -> sswap:
        """Swap memory"""
        return swap_memory()

    def virtual(self) -> NamedTuple:  # svmem:
        """Virtual memory"""
        return virtual_memory()


class MemoryUpdate(ModuleUpdateBase):
    """Memory Update"""

    def __init__(
        self,
        database: Database,
    ) -> None:
        """Initialize"""
        super().__init__(database)
        self._memory = Memory()

    async def update_swap(self) -> None:
        """Update Swap Memory"""
        for key, value in self._memory.swap()._asdict().items():
            self._database.update_data(
                DatabaseModel,
                DatabaseModel(
                    key=f"swap_{key}",
                    value=value,
                ),
            )

    async def update_virtual(self) -> None:
        """Update Virtual Memory"""
        for key, value in self._memory.virtual()._asdict().items():
            self._database.update_data(
                DatabaseModel,
                DatabaseModel(
                    key=f"virtual_{key}",
                    value=value,
                ),
            )

    async def update_all_data(self) -> None:
        """Update data"""
        await asyncio.gather(
            *[
                self.update_swap(),
                self.update_virtual(),
            ]
        )
