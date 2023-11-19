"""System Bridge: Modules"""
import asyncio
from collections.abc import Awaitable, Callable

from systembridgemodels.data import Data
from systembridgeshared.base import Base

from .battery import BatteryUpdate
from .cpu import CPUUpdate
from .disk import DiskUpdate
from .display import DisplayUpdate
from .gpu import GPUUpdate
from .memory import MemoryUpdate
from .network import NetworkUpdate
from .processes import ProcessesUpdate
from .sensors import SensorsUpdate
from .system import SystemUpdate

MODULES = [
    "battery",
    "cpu",
    "disk",
    "display",
    "gpu",
    "media",
    "memory",
    "network",
    "processes",
    "sensors",
    "system",
]


class Update(Base):
    """Modules Update"""

    def __init__(
        self,
        updated_callback: Callable[[str], Awaitable[Data]],
    ) -> None:
        """Initialize"""
        super().__init__()
        self.updated_callback = updated_callback

        self._classes = [
            {"name": "battery", "cls": BatteryUpdate()},
            {"name": "disk", "cls": DiskUpdate()},
            {"name": "system", "cls": SystemUpdate()},
        ]
        self._classes_frequent = [
            {"name": "cpu", "cls": CPUUpdate()},
            {"name": "display", "cls": DisplayUpdate()},
            {"name": "gpu", "cls": GPUUpdate()},
            {"name": "memory", "cls": MemoryUpdate()},
            {"name": "network", "cls": NetworkUpdate()},
            {"name": "processes", "cls": ProcessesUpdate()},
        ]

    async def _update(
        self,
        class_obj: dict,
    ) -> None:
        """Update"""
        await class_obj["cls"].update_all_data()
        await self.updated_callback(class_obj["name"])

    async def update_data(self) -> None:
        """Update Data"""
        self._logger.info("Update data")

        tasks = [self._update(cls) for cls in self._classes]
        await asyncio.gather(*tasks)

        self._logger.info("Finished updating data")

    async def update_frequent_data(self) -> None:
        """Update Data"""
        self._logger.info("Update frequent data")

        sensors_update = SensorsUpdate()
        await sensors_update.update_all_data()
        await self.updated_callback("sensors")

        tasks = [self._update(cls) for cls in self._classes_frequent]
        await asyncio.gather(*tasks)

        self._logger.info("Finished updating frequent data")
        return data
