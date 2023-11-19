"""System Bridge: CPU"""
from __future__ import annotations

import asyncio
from typing import override

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

    async def _get_count(self) -> int:
        """CPU count"""
        return cpu_count()

    async def _get_frequency(self) -> scpufreq:
        """CPU frequency"""
        return cpu_freq()

    async def _get_frequency_per_cpu(
        self,
    ) -> list[scpufreq]:  # pylint: disable=unsubscriptable-object
        """CPU frequency per CPU"""
        return cpu_freq(percpu=True)  # type: ignore

    async def _get_load_average(
        self,
    ) -> tuple[float, float, float]:  # pylint: disable=unsubscriptable-object
        """Get load average"""
        return getloadavg()

    async def _get_power_package(self) -> float | None:
        """CPU package power"""
        # TODO: Find in sensor data
        return None

    async def _get_power_per_cpu(self) -> list[tuple[int, float]] | None:
        """CPU package power"""
        # TODO: Find in sensor data
        return None

    async def _get_stats(self) -> scpustats:
        """CPU stats"""
        return cpu_stats()

    async def _get_temperature(self) -> float | None:
        """CPU temperature"""
        # TODO: Find in sensor data
        return None

    async def _get_times(self) -> pcputimes:
        """CPU times"""
        return cpu_times(percpu=False)

    async def _get_times_percent(self) -> pcputimes:
        """CPU times percent"""
        return cpu_times_percent(interval=1, percpu=False)

    async def _get_times_per_cpu(
        self,
    ) -> list[pcputimes]:  # pylint: disable=unsubscriptable-object
        """CPU times per CPU"""
        return cpu_times(percpu=True)

    async def _get_times_per_cpu_percent(
        self,
    ) -> list[pcputimes]:  # pylint: disable=unsubscriptable-object
        """CPU times per CPU percent"""
        return cpu_times_percent(interval=1, percpu=True)

    async def _get_usage(self) -> float:
        """CPU usage"""
        return cpu_percent(interval=1, percpu=False)

    async def _get_usage_per_cpu(
        self,
    ) -> list[float]:  # pylint: disable=unsubscriptable-object
        """CPU usage per CPU"""
        return cpu_percent(interval=1, percpu=True)  # type: ignore

    async def _get_voltage(self) -> float | None:
        """CPU voltage"""
        # TODO: Find in sensor data
        # for item in database.get_data(SensorsDatabaseModel):
        #     if (
        #         item.hardware_type is not None
        #         and "cpu" in item.hardware_type.lower()
        #         and "voltage" in item.type.lower()
        #     ):
        #         self._logger.debug("Found CPU voltage: %s = %s", item.key, item.value)
        #         return item.value
        return None

    @override
    async def update_all_data(self) -> CPU:
        """Update all data"""
        self._logger.debug("Update all data")
        (
            count,
            frequency,
            frequency_per_cpu,
            load_average,
            power_package,
            power_per_cpu,
            stats,
            temperature,
            times,
            times_percent,
            times_per_cpu,
            times_per_cpu_percent,
            usage,
            usage_per_cpu,
            voltage,
        ) = await asyncio.gather(
            *[
                self._get_count(),
                self._get_frequency(),
                self._get_frequency_per_cpu(),
                self._get_load_average(),
                self._get_power_package(),
                self._get_power_per_cpu(),
                self._get_stats(),
                self._get_temperature(),
                self._get_times(),
                self._get_times_percent(),
                self._get_times_per_cpu(),
                self._get_times_per_cpu_percent(),
                self._get_usage(),
                self._get_usage_per_cpu(),
                self._get_voltage(),
            ]
        )

        return CPU(
            count=count,
            frequency_current=frequency.current,
            frequency_min=frequency.min,
            frequency_max=frequency.max,
            # frequency_per_cpu=frequency_per_cpu,
            load_average=load_average,
            power_package=power_package,
            # power_per_cpu=power_per_cpu,
            stats_ctx_switches=stats.ctx_switches,
            stats_interrupts=stats.interrupts,
            stats_soft_interrupts=stats.soft_interrupts,
            stats_syscalls=stats.syscalls,
            temperature=temperature,
            times_user=times.user,
            times_system=times.system,
            times_idle=times.idle,
            times_interrupt=times.interrupt,
            times_dpc=times.dpc,
            times_percent_user=times_percent.user,
            times_percent_system=times_percent.system,
            times_percent_idle=times_percent.idle,
            times_percent_interrupt=times_percent.interrupt,
            times_percent_dpc=times_percent.dpc,
            # times_per_cpu=times_per_cpu,
            usage=usage,
            # usage_per_cpu=usage_per_cpu,
            voltage=voltage,
        )
