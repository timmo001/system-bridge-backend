"""GPUs."""

from typing import override

from systembridgemodels.modules.gpus import GPU
from systembridgemodels.modules.sensors import Sensors

from .base import ModuleUpdateBase


class GPUsUpdate(ModuleUpdateBase):
    """GPUs Update."""

    def __init__(self) -> None:
        """Initialise."""
        super().__init__()
        self.sensors: Sensors | None = None

    @override
    async def update_all_data(self) -> list[GPU]:
        """Update all data."""
        self._logger.debug("Update all data")

        if (
            self.sensors is None
            or self.sensors.windows_sensors is None
            or self.sensors.windows_sensors.hardware is None
        ):
            return []

        gpus: list[GPU] = []

        for hardware in self.sensors.windows_sensors.hardware:
            hardware_type = hardware.type.upper()
            if "GPU" not in hardware_type:
                continue

            self._logger.debug("Found GPU: %s (%s)", hardware.name, hardware.type)

            gpu = GPU(
                id=hardware.id,
                name=hardware.name,
            )

            for sensor in hardware.sensors:
                sensor_name = sensor.name.upper()
                sensor_type = sensor.type.upper()
                # Find "CLOCK" in type and "CORE" in name
                if "CLOCK" in sensor_type and "CORE" in sensor_name:
                    self._logger.debug(
                        "Found GPU core clock: %s (%s) = %s",
                        sensor_name,
                        sensor_type,
                        sensor.value,
                    )
                    gpu.core_clock = float(sensor.value) if sensor.value else None
                # Find "LOAD" in type and "CORE" in name
                elif "LOAD" in sensor_type and "CORE" in sensor_name:
                    self._logger.debug(
                        "Found GPU core load: %s (%s) = %s",
                        sensor_name,
                        sensor_type,
                        sensor.value,
                    )
                    gpu.core_load = float(sensor.value) if sensor.value else None
                # Find "FAN" in type
                elif "FAN" in sensor_type:
                    self._logger.debug(
                        "Found GPU fan speed: %s (%s) = %s",
                        sensor_name,
                        sensor_type,
                        sensor.value,
                    )
                    # Only use the first fan speed or if the fan speed is None
                    if sensor.id.endswith("1") or gpu.fan_speed is None:
                        gpu.fan_speed = (
                            float(sensor.value) if sensor.value is not None else None
                        )
                # Find "CLOCK" in type and "MEMORY" in name
                elif "CLOCK" in sensor_type and "MEMORY" in sensor_name:
                    self._logger.debug(
                        "Found GPU memory clock: %s (%s) = %s",
                        sensor_name,
                        sensor_type,
                        sensor.value,
                    )
                    gpu.memory_clock = float(sensor.value) if sensor.value else None
                # Find "LOAD" in type and "MEMORY" in name
                elif "LOAD" in sensor_type and "MEMORY" in sensor_name:
                    self._logger.debug(
                        "Found GPU memory load: %s (%s) = %s",
                        sensor_name,
                        sensor_type,
                        sensor.value,
                    )
                    gpu.memory_load = float(sensor.value) if sensor.value else None
                # Find "FREE" and "MEMORY" in name
                elif "FREE" in sensor_name and "MEMORY" in sensor_name:
                    self._logger.debug(
                        "Found GPU memory free: %s (%s) = %s",
                        sensor_name,
                        sensor_type,
                        sensor.value,
                    )
                    gpu.memory_free = float(sensor.value) if sensor.value else None
                # Find "USED" and "MEMORY" in name
                elif "USED" in sensor_name and "MEMORY" in sensor_name:
                    self._logger.debug(
                        "Found GPU memory used: %s (%s) = %s",
                        sensor_name,
                        sensor_type,
                        sensor.value,
                    )
                    gpu.memory_used = float(sensor.value) if sensor.value else None
                # Find "TOTAL" and "MEMORY" in name
                elif "TOTAL" in sensor_name and "MEMORY" in sensor_name:
                    self._logger.debug(
                        "Found GPU memory total: %s (%s) = %s",
                        sensor_name,
                        sensor_type,
                        sensor.value,
                    )
                    gpu.memory_total = float(sensor.value) if sensor.value else None
                # Find "POWER" in name
                elif "POWER" in sensor_name:
                    self._logger.debug(
                        "Found GPU power: %s (%s) = %s",
                        sensor_name,
                        sensor_type,
                        sensor.value,
                    )
                    gpu.power_usage = float(sensor.value) if sensor.value else None
                # Find "TEMPERATURE" and "CORE" in name
                elif "TEMPERATURE" in sensor_type and "CORE" in sensor_name:
                    self._logger.debug(
                        "Found GPU temperature: %s (%s) = %s",
                        sensor_name,
                        sensor_type,
                        sensor.value,
                    )
                    gpu.temperature = float(sensor.value) if sensor.value else None

            gpus.append(gpu)

        return gpus
