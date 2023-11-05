"""System Bridge: CPU"""
from __future__ import annotations

import asyncio
from typing import Optional

from psutil import (
    cpu_count,
    cpu_freq,
    cpu_percent,
    cpu_stats,
    cpu_times,
    cpu_times_percent,
    getloadavg,
)
from psutil._common import pcputimes, scpufreq, scpustats
from systembridgeshared.base import Base
from systembridgeshared.database import Database
from systembridgeshared.models.database_data import CPU as DatabaseModel
from systembridgeshared.models.database_data_sensors import (
    Sensors as SensorsDatabaseModel,
)

from .base import ModuleUpdateBase


class CPU(Base):
    """CPU"""

    def count(self) -> int:
        """CPU count"""
        return cpu_count()

    def freq(self) -> scpufreq:
        """CPU frequency"""
        return cpu_freq()

    def freq_per_cpu(self) -> list[scpufreq]:  # pylint: disable=unsubscriptable-object
        """CPU frequency per CPU"""
        return cpu_freq(percpu=True)  # type: ignore

    def load_average(
        self,
    ) -> tuple[float, float, float]:  # pylint: disable=unsubscriptable-object
        """Get load average"""
        return getloadavg()

    def power_package(
        self,
        database: Database,
    ) -> Optional[float]:
        """CPU package power"""
        for item in database.get_data(SensorsDatabaseModel):
            if (
                item.hardware_type is not None
                and "cpu" in item.hardware_type.lower()
                and "power" in item.type.lower()
                and "package" in item.name.lower()
            ):
                self._logger.debug(
                    "Found CPU package power: %s = %s", item.key, item.value
                )
                return item.value
        return None

    def power_per_cpu(
        self,
        database: Database,
    ) -> Optional[list[tuple[int, float]]]:
        """CPU package power"""
        result: list[tuple[int, float]] = []
        for item in database.get_data(SensorsDatabaseModel):
            if (
                item.hardware_type is not None
                and "cpu" in item.hardware_type.lower()
                and "power" in item.type.lower()
                and "core" in item.name.lower()
            ):
                key: int = int(item.key.split("#")[1].split("_")[0])
                self._logger.debug(
                    "Found per CPU power: %s (%s) = %s", key, item.key, item.value
                )
                if key is not None:
                    result.append((key - 1, item.value))
        self._logger.debug("Per CPU power result: %s", result)
        if len(result) > 0:
            return result
        return None

    def stats(self) -> scpustats:
        """CPU stats"""
        return cpu_stats()

    def temperature(
        self,
        database: Database,
    ) -> Optional[float]:
        """CPU temperature"""
        for item in database.get_data(SensorsDatabaseModel):
            if item.hardware_type is not None and (
                (
                    "cpu" in item.hardware_type.lower()
                    and "temperature" in item.type.lower()
                )
                or (
                    "k10temp" in item.hardware_type.lower()
                    and "current" in item.type.lower()
                )
            ):
                self._logger.debug(
                    "Found CPU temperature: %s = %s",
                    item.key,
                    item.value,
                )
                return item.value
        return None

    def times(self) -> pcputimes:
        """CPU times"""
        return cpu_times(percpu=False)

    def times_percent(self) -> pcputimes:
        """CPU times percent"""
        return cpu_times_percent(interval=1, percpu=False)

    def times_per_cpu(
        self,
    ) -> list[pcputimes]:  # pylint: disable=unsubscriptable-object
        """CPU times per CPU"""
        return cpu_times(percpu=True)

    def times_per_cpu_percent(
        self,
    ) -> list[pcputimes]:  # pylint: disable=unsubscriptable-object
        """CPU times per CPU percent"""
        return cpu_times_percent(interval=1, percpu=True)

    def usage(self) -> float:
        """CPU usage"""
        return cpu_percent(interval=1, percpu=False)

    def usage_per_cpu(self) -> list[float]:  # pylint: disable=unsubscriptable-object
        """CPU usage per CPU"""
        return cpu_percent(interval=1, percpu=True)  # type: ignore

    def voltage(
        self,
        database: Database,
    ) -> Optional[float]:
        """CPU voltage"""
        for item in database.get_data(SensorsDatabaseModel):
            if (
                item.hardware_type is not None
                and "cpu" in item.hardware_type.lower()
                and "voltage" in item.type.lower()
            ):
                self._logger.debug("Found CPU voltage: %s = %s", item.key, item.value)
                return item.value
        return None


class CPUUpdate(ModuleUpdateBase):
    """CPU Update"""

    def __init__(
        self,
        database: Database,
    ) -> None:
        """Initialize"""
        super().__init__(database)
        self._cpu = CPU()

    async def update_count(self) -> None:
        """Update CPU count"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="count",
                value=str(self._cpu.count()),
            ),
        )

    async def update_frequency(self) -> None:
        """Update CPU frequency"""
        for key, value in self._cpu.freq()._asdict().items():
            self._database.update_data(
                DatabaseModel,
                DatabaseModel(
                    key=f"frequency_{key}",
                    value=value,
                ),
            )

    async def update_frequency_per_cpu(self) -> None:
        """Update CPU frequency per CPU"""
        count = 0
        for data in [freq._asdict() for freq in self._cpu.freq_per_cpu()]:
            for key, value in data.items():
                self._database.update_data(
                    DatabaseModel,
                    DatabaseModel(
                        key=f"frequency_{count}_{key}",
                        value=value,
                    ),
                )
            count += 1

    async def update_load_average(self) -> None:
        """Update load average"""
        avg_tuple = self._cpu.load_average()
        result = sum([avg_tuple[0], avg_tuple[1], avg_tuple[2]]) / 3
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="load_average",
                value=str(result),
            ),
        )

    async def update_power_package(self) -> None:
        """Update package power"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="power_package",
                value=str(self._cpu.power_package(self._database)),
            ),
        )

    async def update_power_per_cpu(self) -> None:
        """Update per cpu power"""
        if (result := self._cpu.power_per_cpu(self._database)) is None:
            return None
        for key, value in result:
            self._database.update_data(
                DatabaseModel,
                DatabaseModel(
                    key=f"power_per_cpu_{key}",
                    value=str(value),
                ),
            )

    async def update_stats(self) -> None:
        """Update stats"""
        for key, value in self._cpu.stats()._asdict().items():
            self._database.update_data(
                DatabaseModel,
                DatabaseModel(
                    key=f"stats_{key}",
                    value=value,
                ),
            )

    async def update_temperature(self) -> None:
        """Update temperature"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="temperature",
                value=str(self._cpu.temperature(self._database)),
            ),
        )

    async def update_times(self) -> None:
        """Update times"""
        for key, value in self._cpu.times()._asdict().items():
            self._database.update_data(
                DatabaseModel,
                DatabaseModel(
                    key=f"times_{key}",
                    value=value,
                ),
            )

    async def update_times_percent(self) -> None:
        """Update times percent"""
        for key, value in self._cpu.times_percent()._asdict().items():
            self._database.update_data(
                DatabaseModel,
                DatabaseModel(
                    key=f"times_percent_{key}",
                    value=value,
                ),
            )

    async def update_times_per_cpu(self) -> None:
        """Update times per CPU"""
        count = 0
        for data in [freq._asdict() for freq in self._cpu.times_per_cpu()]:
            for key, value in data.items():
                self._database.update_data(
                    DatabaseModel,
                    DatabaseModel(
                        key=f"times_per_cpu_{count}_{key}",
                        value=value,
                    ),
                )
            count += 1

    async def update_times_per_cpu_percent(self) -> None:
        """Update times per CPU percent"""
        count = 0
        for data in [freq._asdict() for freq in self._cpu.times_per_cpu_percent()]:
            for key, value in data.items():
                self._database.update_data(
                    DatabaseModel,
                    DatabaseModel(
                        key=f"times_per_cpu_percent_{count}_{key}",
                        value=value,
                    ),
                )
            count += 1

    async def update_usage(self) -> None:
        """Update usage"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="usage",
                value=str(self._cpu.usage()),
            ),
        )

    async def update_usage_per_cpu(self) -> None:
        """Update usage per CPU"""
        count = 0
        for value in self._cpu.usage_per_cpu():
            self._database.update_data(
                DatabaseModel,
                DatabaseModel(
                    key=f"usage_{count}",
                    value=str(value),
                ),
            )
            count += 1

    async def update_voltage(self) -> None:
        """Update voltage"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key="voltage",
                value=str(self._cpu.voltage(self._database)),
            ),
        )

    async def update_all_data(self) -> None:
        """Update data"""
        await asyncio.gather(
            *[
                self.update_count(),
                self.update_frequency(),
                self.update_frequency_per_cpu(),
                self.update_load_average(),
                self.update_power_package(),
                self.update_power_per_cpu(),
                self.update_stats(),
                self.update_temperature(),
                self.update_times(),
                self.update_times_percent(),
                self.update_times_per_cpu(),
                self.update_times_per_cpu_percent(),
                self.update_usage(),
                self.update_usage_per_cpu(),
                self.update_voltage(),
            ]
        )
