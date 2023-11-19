"""System Bridge: CPU"""
from __future__ import annotations

import asyncio
from typing import Any, override

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
from systembridgemodels.cpu import CPU

from .base import ModuleUpdateBase


class CPUUpdate(ModuleUpdateBase):
    """CPU Update"""

    async def _count(self) -> int:
        """CPU count"""
        return cpu_count()

    async def _frequency(self) -> scpufreq:
        """CPU frequency"""
        return cpu_freq()

    async def _frequency_per_cpu(
        self,
    ) -> list[scpufreq]:  # pylint: disable=unsubscriptable-object
        """CPU frequency per CPU"""
        return cpu_freq(percpu=True)  # type: ignore

    async def _load_average(
        self,
    ) -> tuple[float, float, float]:  # pylint: disable=unsubscriptable-object
        """Get load average"""
        return getloadavg()

    async def _power_package(self) -> float | None:
        """CPU package power"""
        # TODO: Find in sensor data
        return None

    async def _power_per_cpu(self) -> list[tuple[int, float]] | None:
        """CPU package power"""
        # TODO: Find in sensor data
        return None

    async def _stats(self) -> scpustats:
        """CPU stats"""
        return cpu_stats()

    async def _temperature(self) -> float | None:
        """CPU temperature"""
        # TODO: Find in sensor data
        return None

    async def _times(self) -> pcputimes:
        """CPU times"""
        return cpu_times(percpu=False)

    async def _times_percent(self) -> pcputimes:
        """CPU times percent"""
        return cpu_times_percent(interval=1, percpu=False)

    async def _times_per_cpu(
        self,
    ) -> list[pcputimes]:  # pylint: disable=unsubscriptable-object
        """CPU times per CPU"""
        return cpu_times(percpu=True)

    async def _times_per_cpu_percent(
        self,
    ) -> list[pcputimes]:  # pylint: disable=unsubscriptable-object
        """CPU times per CPU percent"""
        return cpu_times_percent(interval=1, percpu=True)

    async def _usage(self) -> float:
        """CPU usage"""
        return cpu_percent(interval=1, percpu=False)

    async def _usage_per_cpu(self) -> list[float]:  # pylint: disable=unsubscriptable-object
        """CPU usage per CPU"""
        return cpu_percent(interval=1, percpu=True)  # type: ignore

    async def _voltage(self) -> float | None:
        """CPU voltage"""
        # TODO: Find in sensor data
        return None

    @override
    async def update_all_data(self) -> CPU:
        """Update all data"""
        self._logger.debug("Update all data")
        data = await asyncio.gather(
            *[
                self._count(),
                self._frequency(),
                self._frequency_per_cpu(),
                self._load_average(),
                self._power_package(),
                self._power_per_cpu(),
                self._stats(),
                self._temperature(),
                self._times(),
                self._times_percent(),
                self._times_per_cpu(),
                self._times_per_cpu_percent(),
                self._usage(),
                self._usage_per_cpu(),
                self._voltage(),
            ]
        )

        return CPU(*data)
