"""Modules."""
import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
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


@dataclass
class ModuleClass:
    """Module Class."""

    name: str
    cls: Any


class UpdateDataThread(Thread, Base):
    """Update data thread."""

    def __init__(
        self,
        class_obj: ModuleClass,
        updated_callback: Callable[[str, Any], Awaitable[None]],
    ) -> None:
        """Initialise."""
        Thread.__init__(self)
        Base.__init__(self)
        self._module_class = class_obj
        self._updated_callback = updated_callback

    async def _update(self) -> None:
        """Update."""
        data = await self._module_class.cls.update_all_data()
        await self._updated_callback(self._module_class.name, data)

    def run(self) -> None:
        """Run."""
        try:
            asyncio.run(self._update())
        except Exception as exception:  # pylint: disable=broad-except
            self._logger.exception(exception)


class ModulesUpdate(Base):
    """Modules Update."""

    def __init__(
        self,
        updated_callback: Callable[[str, Any], Awaitable[None]],
    ) -> None:
        """Initialise."""
        super().__init__()
        self._updated_callback = updated_callback

        self._classes: list[ModuleClass] = [
            ModuleClass(name="system", cls=SystemUpdate()),
            ModuleClass(name="battery", cls=BatteryUpdate()),
            ModuleClass(name="cpu", cls=CPUUpdate()),
            ModuleClass(name="disks", cls=DisksUpdate()),
            ModuleClass(name="displays", cls=DisplaysUpdate()),
            ModuleClass(name="gpus", cls=GPUsUpdate()),
            ModuleClass(name="memory", cls=MemoryUpdate()),
            ModuleClass(name="networks", cls=NetworksUpdate()),
            ModuleClass(name="processes", cls=ProcessesUpdate()),
        ]

        self.threads: dict[str, Thread] = {}

    async def update_data(self) -> None:
        """Update Data."""
        self._logger.info("Request update data")

        sensors_update = SensorsUpdate()
        sensors_data = await sensors_update.update_all_data()
        await self._updated_callback("sensors", sensors_data)

        for module_class in self._classes:
            # If the class has a sensors attribute, set it
            if module_class.name == "system":
                module_class.cls.sensors = sensors_data

            self.threads[module_class.name] = UpdateDataThread(
                module_class,
                self._updated_callback,
            )
            self.threads[module_class.name].start()

            # Stagger the updates to avoid overloading the system
            await asyncio.sleep(1)

        self._logger.info("Data update threads started")
