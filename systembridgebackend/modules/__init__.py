"""Modules"""
import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from systembridgemodels.sensors import Sensors
from systembridgeshared.base import Base

from .battery import BatteryUpdate
from .cpu import CPUUpdate
from .disks import DisksUpdate
from .displays import DisplaysUpdate
from .gpus import GPUsUpdate
from .memory import MemoryUpdate
from .networks import NetworksUpdate
from .processes import ProcessesUpdate
from .sensors import SensorsUpdate
from .system import SystemUpdate

MODULES = [
    "battery",
    "cpu",
    "disks",
    "displays",
    "gpus",
    "media",
    "memory",
    "networks",
    "processes",
    "sensors",
    "system",
]


class Update(Base):
    """Modules Update"""

    def __init__(
        self,
        updated_callback: Callable[[str, Any], Awaitable[None]],
    ) -> None:
        """Initialise"""
        super().__init__()
        self._updated_callback = updated_callback

        self._classes = [
            {"name": "battery", "cls": BatteryUpdate()},
            {"name": "cpu", "cls": CPUUpdate()},
            {"name": "disks", "cls": DisksUpdate()},
            {"name": "displays", "cls": DisplaysUpdate()},
            {"name": "gpus", "cls": GPUsUpdate()},
            {"name": "memory", "cls": MemoryUpdate()},
            {"name": "networks", "cls": NetworksUpdate()},
            {"name": "processes", "cls": ProcessesUpdate()},
            {"name": "system", "cls": SystemUpdate()},
        ]

    async def _update(
        self,
        sensors_data: Sensors,
        class_obj: dict,
    ) -> None:
        """Update"""
        # If the class has a sensors attribute, set it
        if class_obj["cls"].__dict__.get("sensors", {}) != {}:
            class_obj["cls"].sensors = sensors_data

        data = await class_obj["cls"].update_all_data()
        await self._updated_callback(
            class_obj["name"],
            data,
        )

    async def update_data(self) -> None:
        """Update Data"""
        self._logger.info("Update data")

        sensors_update = SensorsUpdate()
        sensors_data = await sensors_update.update_all_data()
        await self._updated_callback("sensors", sensors_data)

        # TODO: Update data in separate threads
        tasks = [self._update(sensors_data, cls) for cls in self._classes]
        await asyncio.gather(*tasks)

        self._logger.info("Finished updating data")
