"""CPU."""

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

from systembridgemodels.modules.cpu import CPU, CPUFrequency, CPUStats, CPUTimes, PerCPU
from systembridgemodels.modules.sensors import Sensors

from .base import ModuleUpdateBase


class CPUUpdate(ModuleUpdateBase):
    """CPU Update."""

    def __init__(self) -> None:
        """Initialise."""
        super().__init__()

        self._count: int = cpu_count()

        self.sensors: Sensors | None = None

    async def _get_frequency(self) -> scpufreq:
        """CPU frequency."""
        return cpu_freq()

    async def _get_frequency_per_cpu(
        self,
    ) -> list[scpufreq]:
        """CPU frequency per CPU."""
        return cpu_freq(percpu=True)  # type: ignore

    async def _get_load_average(self) -> float:
        """Get load average."""
        avg_tuple = getloadavg()
        return sum([avg_tuple[0], avg_tuple[1], avg_tuple[2]]) / 3

    async def _get_power_package(self) -> float | None:
        """CPU package power."""
        if (
            self.sensors is None
            or self.sensors.windows_sensors is None
            or self.sensors.windows_sensors.hardware is None
        ):
            return None
        for hardware in self.sensors.windows_sensors.hardware:
            # Find type "CPU"
            if "CPU" not in hardware.type.upper():
                continue
            for sensor in hardware.sensors:
                # Find type "POWER" and name "PACKAGE"
                if (
                    "POWER" in sensor.type.upper()
                    and "PACKAGE" in sensor.name.upper()
                    and sensor.value is not None
                ):
                    self._logger.debug(
                        "Found CPU package power: %s = %s", sensor.name, sensor.value
                    )
                    return (
                        float(sensor.value)
                        if isinstance(sensor.value, (int, float))
                        else None
                    )
        return None

    async def _get_power_per_cpu(self) -> list[float] | None:
        """CPU package power."""
        powers: list[float] = [-1] * self._count
        if (
            self.sensors is None
            or self.sensors.windows_sensors is None
            or self.sensors.windows_sensors.hardware is None
        ):
            return None
        for hardware in self.sensors.windows_sensors.hardware:
            # Find type "CPU"
            if "CPU" not in hardware.type.upper():
                continue
            for sensor in hardware.sensors:
                # Find type "POWER" and name "CORE"
                if (
                    "POWER" in sensor.type.upper()
                    and "CORE" in sensor.name.upper()
                    and sensor.value is not None
                ):
                    self._logger.debug(
                        "Found CPU core power: %s (%s) = %s",
                        sensor.name,
                        sensor.id,
                        sensor.value,
                    )
                    for sensor in hardware.sensors:
                        # Find type "POWER" and name "PACKAGE"
                        if (
                            "POWER" in sensor.type.upper()
                            and "PACKAGE" not in sensor.name.upper()
                            and sensor.value is not None
                        ):
                            self._logger.debug(
                                "Found CPU package power: %s (%s) = %s",
                                sensor.name,
                                sensor.id,
                                sensor.value,
                            )
                            index = int(sensor.id.split("/")[-1])
                            powers[index] = float(sensor.value)

        return powers

    async def _get_stats(self) -> scpustats:
        """CPU stats."""
        return cpu_stats()

    async def _get_temperature(self) -> float | None:
        """CPU temperature."""
        if (
            self.sensors is None
            or self.sensors.windows_sensors is None
            or self.sensors.windows_sensors.hardware is None
        ):
            return None
        for hardware in self.sensors.windows_sensors.hardware:
            # Find type "CPU"
            if "CPU" not in hardware.type.upper():
                continue
            for sensor in hardware.sensors:
                name = sensor.name.upper()
                # Find type "TEMPERATURE" and name "PACKAGE" or "AVERAGE"
                if (
                    "TEMPERATURE" in sensor.type.upper()
                    and ("PACKAGE" in name or "AVERAGE" in name)
                    and sensor.value is not None
                ):
                    self._logger.debug(
                        "Found CPU temperature: %s = %s", sensor.name, sensor.value
                    )
                    return (
                        float(sensor.value)
                        if isinstance(sensor.value, (int, float, str))
                        else None
                    )
        return None

    async def _get_times(self) -> pcputimes:
        """CPU times."""
        return cpu_times(percpu=False)

    async def _get_times_percent(self) -> pcputimes:
        """CPU times percent."""
        return cpu_times_percent(interval=1, percpu=False)

    async def _get_times_per_cpu(
        self,
    ) -> list[pcputimes]:
        """CPU times per CPU."""
        return cpu_times(percpu=True)

    async def _get_times_per_cpu_percent(
        self,
    ) -> list[pcputimes]:
        """CPU times per CPU percent."""
        return cpu_times_percent(interval=1, percpu=True)

    async def _get_usage(self) -> float:
        """CPU usage."""
        return cpu_percent(interval=1, percpu=False)

    async def _get_usage_per_cpu(
        self,
    ) -> list[float]:
        """CPU usage per CPU."""
        return cpu_percent(interval=1, percpu=True)  # type: ignore

    async def _get_voltages(self) -> tuple[float | None, list[float]]:
        """CPU voltage."""
        voltage: float | None = None
        voltages: list[float] = [-1] * self._count
        voltage_sensors = []
        if (
            self.sensors is None
            or self.sensors.windows_sensors is None
            or self.sensors.windows_sensors.hardware is None
        ):
            return (voltage, voltages)
        for hardware in self.sensors.windows_sensors.hardware:
            # Find type "CPU"
            if "CPU" not in hardware.type.upper():
                continue
            for sensor in hardware.sensors:
                # Find type "VOLTAGE"
                if "VOLTAGE" in sensor.type.upper() and sensor.value is not None:
                    self._logger.debug(
                        "Found CPU voltage: %s (%s) = %s",
                        sensor.name,
                        sensor.id,
                        sensor.value,
                    )
                    voltage_sensors.append(sensor)

        # Handle voltages
        if voltage_sensors is not None and len(voltage_sensors) > 0:
            for sensor in voltage_sensors:
                if sensor.value is not None:
                    self._logger.debug(
                        "CPU voltage: %s (%s) = %s",
                        sensor.name,
                        sensor.type,
                        sensor.value,
                    )
                    # "/amdcpu/0/voltage/16" -> 16
                    # Get the last part of the id
                    index = int(sensor.id.split("/")[-1])
                    if 0 <= index < self._count:
                        voltages[index] = float(sensor.value)
            voltage_sum = 0
            for voltage in voltages:
                if voltage is not None:
                    voltage_sum += voltage
            if voltage_sum > 0:
                voltage = voltage_sum / self._count
            else:
                # If we can't get the average, just use the first value
                voltage = voltage_sensors[0].value

        return (voltage, voltages)

    @override
    async def update_all_data(self) -> CPU:
        """Update all data."""
        self._logger.debug("Update all data")

        self._count = cpu_count()

        (
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
            [voltage, voltages],
        ) = await asyncio.gather(
            *[
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
                self._get_voltages(),
            ]
        )

        return CPU(
            count=self._count,
            frequency=CPUFrequency(
                current=frequency.current,
                min=frequency.min,
                max=frequency.max,
            ),
            load_average=load_average,
            per_cpu=[
                PerCPU(
                    id=index,
                    frequency=CPUFrequency(
                        current=frequency_per_cpu[index].current,
                        min=frequency_per_cpu[index].min,
                        max=frequency_per_cpu[index].max,
                    )
                    if frequency_per_cpu is not None and index < len(frequency_per_cpu)
                    else None,
                    power=power_per_cpu[index]
                    if power_per_cpu is not None
                    and index < len(power_per_cpu)
                    and power_per_cpu[index] > 0
                    else None,
                    times=CPUTimes(
                        user=times_per_cpu[index].user,
                        system=times_per_cpu[index].system,
                        idle=times_per_cpu[index].idle,
                        interrupt=times_per_cpu[index].interrupt
                        if hasattr(times_per_cpu[index], "interrupt")
                        else None,
                        dpc=times_per_cpu[index].dpc
                        if hasattr(times_per_cpu[index], "dpc")
                        else None,
                    )
                    if times_per_cpu is not None and index < len(times_per_cpu)
                    else None,
                    times_percent=CPUTimes(
                        user=times_per_cpu_percent[index].user,
                        system=times_per_cpu_percent[index].system,
                        idle=times_per_cpu_percent[index].idle,
                        interrupt=times_per_cpu_percent[index].interrupt
                        if hasattr(times_per_cpu_percent[index], "interrupt")
                        else None,
                        dpc=times_per_cpu_percent[index].dpc
                        if hasattr(times_per_cpu_percent[index], "dpc")
                        else None,
                    )
                    if times_per_cpu_percent is not None
                    and index < len(times_per_cpu_percent)
                    else None,
                    usage=usage_per_cpu[index]
                    if usage_per_cpu is not None and index < len(usage_per_cpu)
                    else None,
                    voltage=voltages[index]
                    if voltages is not None
                    and index < len(voltages)
                    and voltages[index] > 0
                    else None,
                )
                for index in range(self._count)
            ],
            power=power_package,
            stats=CPUStats(
                ctx_switches=stats.ctx_switches,
                interrupts=stats.interrupts,
                soft_interrupts=stats.soft_interrupts,
                syscalls=stats.syscalls,
            ),
            temperature=temperature,
            times=CPUTimes(
                user=times.user,
                system=times.system,
                idle=times.idle,
                interrupt=times.interrupt if hasattr(times, "interrupt") else None,
                dpc=times.dpc if hasattr(times, "dpc") else None,
            ),
            times_percent=CPUTimes(
                user=times_percent.user,
                system=times_percent.system,
                idle=times_percent.idle,
                interrupt=times_percent.interrupt
                if hasattr(times_percent, "interrupt")
                else None,
                dpc=times_percent.dpc if hasattr(times_percent, "dpc") else None,
            ),
            usage=usage,
            voltage=voltage,
        )
