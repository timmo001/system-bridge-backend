"""Modules."""
import asyncio
from asyncio import Task
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from queue import Queue
import time
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


class ModulesUpdate(Base):
    """Modules Update."""

    def __init__(
        self,
        updated_callback: Callable[[str, Any], Awaitable[None]],
    ) -> None:
        """Initialise."""
        super().__init__()
        self._updated_callback = updated_callback

        self._classes: dict[str, ModuleClass] = dict((m.name, m) for m in [
            ModuleClass(name="system", cls=SystemUpdate()),
            ModuleClass(name="battery", cls=BatteryUpdate()),
            ModuleClass(name="cpu", cls=CPUUpdate()),
            ModuleClass(name="disks", cls=DisksUpdate()),
            ModuleClass(name="displays", cls=DisplaysUpdate()),
            ModuleClass(name="gpus", cls=GPUsUpdate()),
            ModuleClass(name="memory", cls=MemoryUpdate()),
            ModuleClass(name="networks", cls=NetworksUpdate()),
            ModuleClass(name="processes", cls=ProcessesUpdate()),
        ])

        self.tasks: dict[str, Task] = {}

    async def update_module(self, module_class: ModuleClass) -> None:
        """Update Module."""
        time_update_start  = time.perf_counter()
        self._logger.debug("Start update module: %s", module_class.name)

        try:
            module_data = await module_class.cls.update_all_data()
            await self._updated_callback(module_class.name, module_data)
        except Exception as exception:  # pylint: disable=broad-except
            self._logger.exception(
                "Failed to update module: %s",
                module_class.name,
                exc_info=exception,
            )
        self._logger.info(
            "Module updated: %s time=%0.3fs",
            module_class.name,
            time.perf_counter() - time_update_start,
        )

    async def update_data(self, modules: list[str] | None = None) -> None:
        """Update Data."""
        self._logger.info("Update data, modules=%s", modules or 'ALL')

        sensors_update = SensorsUpdate()
        sensors_data = await sensors_update.update_all_data()
        await self._updated_callback("sensors", sensors_data)

        if modules:
            classes = (self._classes[cls] for cls in modules)
        else:
            classes = self._classes.values()

        for module_class in classes:
            # If the class has a sensors attribute, set it
            if hasattr(module_class.cls, "sensors"):
                module_class.cls.sensors = sensors_data

            # If the task is already running, skip it
            if (
                module_class.name in self.tasks
                and not self.tasks[module_class.name].done()
            ):
                self._logger.debug("Skip already running task %s", module_class.name)
                continue

            # Start the task
            try:
                self.tasks[module_class.name] = asyncio.create_task(
                    self.update_module(module_class),
                    name=f"Module Update: {module_class.name}",
                )
            except Exception as exception:  # pylint: disable=broad-except
                self._logger.exception(
                    "Failed to update module: %s",
                    module_class.name,
                    exc_info=exception,
                )

            # Stagger the updates to avoid overloading the system
            await asyncio.sleep(1)

        self._logger.info("Data update tasks started")
