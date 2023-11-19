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

    def count(self) -> int:
        """CPU count"""
        return cpu_count()

    def frequency(self) -> scpufreq:
        """CPU frequency"""
        return cpu_freq()

    def frequency_per_cpu(
        self,
    ) -> list[scpufreq]:  # pylint: disable=unsubscriptable-object
        """CPU frequency per CPU"""
        return cpu_freq(percpu=True)  # type: ignore

    def load_average(
        self,
    ) -> tuple[float, float, float]:  # pylint: disable=unsubscriptable-object
        """Get load average"""
        return getloadavg()

    def power_package(self) -> float | None:
        """CPU package power"""
        # TODO: Find in sensor data
        return None

    def power_per_cpu(self) -> list[tuple[int, float]] | None:
        """CPU package power"""
        # TODO: Find in sensor data
        return None

    def stats(self) -> scpustats:
        """CPU stats"""
        return cpu_stats()

    def temperature(self) -> float | None:
        """CPU temperature"""
        # TODO: Find in sensor data
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

    def voltage(self) -> float | None:
        """CPU voltage"""
        # TODO: Find in sensor data
        return None

    @override
    async def update_all_data(self) -> CPU:
        """Update all data"""
        data = await asyncio.gather(
            *[
                self.count(),
                self.frequency(),
                self.frequency_per_cpu(),
                self.load_average(),
                self.power_package(),
                self.power_per_cpu(),
                self.stats(),
                self.temperature(),
                self.times(),
                self.times_percent(),
                self.times_per_cpu(),
                self.times_per_cpu_percent(),
                self.usage(),
                self.usage_per_cpu(),
                self.voltage(),
            ]
        )

        return CPU(*data)
