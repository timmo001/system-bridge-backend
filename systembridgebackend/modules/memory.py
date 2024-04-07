"""Memory."""

import asyncio
from typing import NamedTuple, override

from psutil import swap_memory, virtual_memory
from psutil._common import sswap

from systembridgemodels.modules.memory import Memory, MemorySwap, MemoryVirtual

from .base import ModuleUpdateBase


class MemoryUpdate(ModuleUpdateBase):
    """Memory Update."""

    async def _get_swap(self) -> sswap:
        """Swap memory."""
        return swap_memory()

    async def _get_virtual(self) -> NamedTuple:
        """Virtual memory."""
        return virtual_memory()

    @override
    async def update_all_data(self) -> Memory:
        """Update all data."""
        self._logger.debug("Update all data")

        swap, virtual = await asyncio.gather(
            *[
                self._get_swap(),
                self._get_virtual(),
            ]
        )

        return Memory(
            swap=MemorySwap(
                free=swap.free,
                percent=swap.percent,
                sin=swap.sin,
                sout=swap.sout,
                total=swap.total,
                used=swap.used,
            ),
            virtual=MemoryVirtual(
                total=virtual.total,
                available=virtual.available,
                percent=virtual.percent,
                used=virtual.used,
                free=virtual.free,
                active=getattr(virtual, "active", None),
                inactive=getattr(virtual, "inactive", None),
                buffers=getattr(virtual, "buffers", None),
                cached=getattr(virtual, "cached", None),
                wired=getattr(virtual, "wired", None),
                shared=getattr(virtual, "shared", None),
            ),
        )
