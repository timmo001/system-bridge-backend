"""GPUs."""
from __future__ import annotations

from typing import override

from systembridgemodels.modules.gpus import GPU, GPUs
from systembridgemodels.modules.sensors import Sensors

from .base import ModuleUpdateBase


class GPUsUpdate(ModuleUpdateBase):
    """GPUs Update."""

    def __init__(self) -> None:
        """Initialise."""
        super().__init__()
        self.sensors: Sensors | None = None

    @override
    async def update_all_data(self) -> GPUs:
        """Update all data."""
        self._logger.debug("Update all data")

        if (
            self.sensors is None
            or self.sensors.windows_sensors is None
            or self.sensors.windows_sensors.hardware is None
        ):
            return []

        gpus: GPUs = []

        for hardware in self.sensors.windows_sensors.hardware:
            # Find type "GPU" and name gpu_key
            if "GPU" not in hardware.type.upper():
                continue

            gpu = GPU(name=hardware.name)

            for sensor in hardware.sensors:
                name = sensor.name.upper()
                # Find "CLOCK" and "CORE" in name
                if "CLOCK" in name and "CORE" in name:
                    self._logger.debug(
                        "Found GPU core clock: %s = %s",
                        sensor.name,
                        sensor.value,
                    )
                    gpu.core_clock = float(sensor.value) if sensor.value else None
                # Find "LOAD" and "CORE" in name
                elif "LOAD" in name and "CORE" in name:
                    self._logger.debug(
                        "Found GPU core load: %s = %s",
                        sensor.name,
                        sensor.value,
                    )
                    gpu.core_load = float(sensor.value) if sensor.value else None
                # Find "FAN" in name
                elif "FAN" in name:
                    self._logger.debug(
                        "Found GPU fan speed: %s = %s",
                        sensor.name,
                        sensor.value,
                    )
                    gpu.fan_speed = float(sensor.value) if sensor.value else None
                # Find "CLOCK" and "MEMORY" in name
                elif "CLOCK" in name and "MEMORY" in name:
                    self._logger.debug(
                        "Found GPU memory clock: %s = %s",
                        sensor.name,
                        sensor.value,
                    )
                    gpu.memory_clock = float(sensor.value) if sensor.value else None
                # Find "LOAD" and "MEMORY" in name
                elif "LOAD" in name and "MEMORY" in name:
                    self._logger.debug(
                        "Found GPU memory load: %s = %s",
                        sensor.name,
                        sensor.value,
                    )
                    gpu.memory_load = float(sensor.value) if sensor.value else None
                # Find "FREE" and "MEMORY" in name
                elif "FREE" in name and "MEMORY" in name:
                    self._logger.debug(
                        "Found GPU memory free: %s = %s",
                        sensor.name,
                        sensor.value,
                    )
                    gpu.memory_free = float(sensor.value) if sensor.value else None
                # Find "USED" and "MEMORY" in name
                elif "USED" in name and "MEMORY" in name:
                    self._logger.debug(
                        "Found GPU memory used: %s = %s",
                        sensor.name,
                        sensor.value,
                    )
                    gpu.memory_used = float(sensor.value) if sensor.value else None
                # Find "TOTAL" and "MEMORY" in name
                elif "TOTAL" in name and "MEMORY" in name:
                    self._logger.debug(
                        "Found GPU memory total: %s = %s",
                        sensor.name,
                        sensor.value,
                    )
                    gpu.memory_total = float(sensor.value) if sensor.value else None
                # Find "POWER" in name
                elif "POWER" in name:
                    self._logger.debug(
                        "Found GPU power: %s = %s",
                        sensor.name,
                        sensor.value,
                    )
                    gpu.power_usage = float(sensor.value) if sensor.value else None
                # Find "TEMPERATURE" and "CORE" in name
                elif "TEMPERATURE" in name and "CORE" in name:
                    self._logger.debug(
                        "Found GPU temperature: %s = %s",
                        sensor.name,
                        sensor.value,
                    )
                    gpu.temperature = float(sensor.value) if sensor.value else None

            gpus.append(gpu)

        return gpus
