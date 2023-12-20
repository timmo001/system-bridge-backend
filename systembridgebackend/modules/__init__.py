"""Modules."""
import asyncio
from collections.abc import Awaitable, Callable
from threading import Thread
from typing import Any

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


class UpdateDataThread(Thread, Base):
    """Update data thread."""

    def __init__(
        self,
        class_obj: dict[str, Any],
        updated_callback: Callable[[str, Any], Awaitable[None]],
    ) -> None:
        """Initialise."""
        Thread.__init__(self)
        Base.__init__(self)
        self._class_obj = class_obj
        self._updated_callback = updated_callback

    async def _update(self) -> None:
        """Update."""
        data = await self._class_obj["cls"].update_all_data()
        await self._updated_callback(
            self._class_obj["name"],
            data,
        )

    def run(self) -> None:
        """Run."""
        try:
            asyncio.run(self._update())
        except Exception as exception:  # pylint: disable=broad-except
            self._logger.exception(exception)


class Update(Base):
    """Modules Update."""

    def __init__(
        self,
        updated_callback: Callable[[str, Any], Awaitable[None]],
    ) -> None:
        """Initialise."""
        super().__init__()
        self._updated_callback = updated_callback

        self._classes: list[dict[str, Any]] = [
            {"name": "system", "cls": SystemUpdate()},
            {"name": "battery", "cls": BatteryUpdate()},
            {"name": "cpu", "cls": CPUUpdate()},
            {"name": "disks", "cls": DisksUpdate()},
            {"name": "displays", "cls": DisplaysUpdate()},
            {"name": "gpus", "cls": GPUsUpdate()},
            {"name": "memory", "cls": MemoryUpdate()},
            {"name": "networks", "cls": NetworksUpdate()},
            {"name": "processes", "cls": ProcessesUpdate()},
        ]

        self.threads: dict[str, Thread] = {}

    async def update_data(self) -> None:
        """Update Data."""
        self._logger.info("Request update data")

        sensors_update = SensorsUpdate()
        sensors_data = await sensors_update.update_all_data()
        await self._updated_callback("sensors", sensors_data)

        for class_obj in self._classes:
            # If the class has a sensors attribute, set it
            if class_obj["cls"].__dict__.get("sensors", {}) != {}:
                class_obj["cls"].sensors = sensors_data

            self.threads[class_obj["name"]] = UpdateDataThread(
                class_obj,
                self._updated_callback,
            )
            self.threads[class_obj["name"]].start()

            # Stagger the updates to avoid overloading the system
            await asyncio.sleep(1)

        self._logger.info("Data updates requested")
