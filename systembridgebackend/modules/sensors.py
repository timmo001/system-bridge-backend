"""Sensors."""

import asyncio
import json
import subprocess
import sys
from typing import Any

import psutil

from systembridgemodels.modules.sensors import (
    Sensors,
    SensorsNVIDIA,
    SensorsNVIDIAChipset,
    SensorsNVIDIADisplay,
    SensorsNVIDIADriver,
    SensorsNVIDIAGPU,
    SensorsWindows,
    SensorsWindowsHardware,
    SensorsWindowsSensor,
)

from .base import ModuleUpdateBase


class SensorsUpdate(ModuleUpdateBase):
    """Sensors Update."""

    async def _get_fans(self) -> Any | None:
        """Get fans."""
        if not hasattr(psutil, "sensors_fans"):
            return None
        return psutil.sensors_fans()  # type: ignore

    async def _get_temperatures(self) -> Any | None:
        """Get temperatures."""
        if not hasattr(psutil, "sensors_temperatures"):
            return None
        return psutil.sensors_temperatures()  # type: ignore

    async def _get_windows_sensors(self) -> dict | None:
        """Get windows sensors."""
        if sys.platform != "win32":
            return None

        try:
            # Import here to not raise error when importing file on linux
            # pylint: disable=import-error, import-outside-toplevel
            from systembridgewindowssensors import get_windowssensors_path
        except (ImportError, ModuleNotFoundError) as exception:
            self._logger.warning("Windows sensors not found", exc_info=exception)
            return None

        path = get_windowssensors_path()

        self._logger.debug("Windows sensors path: %s", path)
        try:
            with subprocess.Popen(
                [path],
                stdout=subprocess.PIPE,
            ) as pipe:
                result = pipe.communicate()[0].decode()
            self._logger.debug("Windows sensors result: %s", result)
        except Exception as exception:  # pylint: disable=broad-except
            self._logger.error(
                "Windows sensors error for path: %s", path, exc_info=exception
            )
            return None

        try:
            return json.loads(result)
        except json.decoder.JSONDecodeError as exception:
            self._logger.error("JSONDecodeError", exc_info=exception)
            return None

    async def update_all_data(self) -> Sensors:
        """Update data."""
        fans, temperatures, windows_sensors = await asyncio.gather(
            *[
                self._get_fans(),
                self._get_temperatures(),
                self._get_windows_sensors(),
            ]
        )

        return Sensors(
            fans=fans,
            temperatures=temperatures,
            windows_sensors=SensorsWindows(
                hardware=[
                    SensorsWindowsHardware(
                        id=hardware["id"],
                        name=hardware["name"],
                        type=hardware["type"],
                        subhardware=[
                            SensorsWindowsHardware(
                                id=subhardware["id"],
                                name=subhardware["name"],
                                type=subhardware["type"],
                                subhardware=[],
                                sensors=[
                                    SensorsWindowsSensor(
                                        id=sensor["id"],
                                        name=sensor["name"],
                                        type=sensor["type"],
                                        value=sensor["value"],
                                    )
                                    for sensor in subhardware["sensors"]
                                ],
                            )
                            for subhardware in hardware["subhardware"]
                        ],
                        sensors=[
                            SensorsWindowsSensor(
                                id=sensor["id"],
                                name=sensor["name"],
                                type=sensor["type"],
                                value=sensor["value"],
                            )
                            for sensor in hardware["sensors"]
                        ],
                    )
                    for hardware in windows_sensors["hardware"]
                ]
                if "hardware" in windows_sensors
                and windows_sensors["hardware"] is not None
                else None,
                nvidia=SensorsNVIDIA(
                    chipset=SensorsNVIDIAChipset(
                        id=windows_sensors["nvidia"]["chipset"]["id"],
                        name=windows_sensors["nvidia"]["chipset"]["name"],
                        flags=windows_sensors["nvidia"]["chipset"]["flags"],
                        vendor_id=windows_sensors["nvidia"]["chipset"]["vendor_id"],
                        vendor_name=windows_sensors["nvidia"]["chipset"]["vendor_name"],
                    ),
                    displays=[
                        SensorsNVIDIADisplay(
                            id=display["id"],
                            name=display["name"],
                            active=display["active"],
                            available=display["available"],
                            connected=display["connected"],
                            dynamic=display["dynamic"],
                            aspect_horizontal=display["aspect_horizontal"],
                            aspect_vertical=display["aspect_vertical"],
                            brightness_current=display["brightness_current"],
                            brightness_default=display["brightness_default"],
                            brightness_max=display["brightness_max"],
                            brightness_min=display["brightness_min"],
                            color_depth=display["color_depth"],
                            connection_type=display["connection_type"],
                            pixel_clock=display["pixel_clock"],
                            refresh_rate=display["refresh_rate"],
                            resolution_horizontal=display["resolution_horizontal"],
                            resolution_vertical=display["resolution_vertical"],
                        )
                        for display in windows_sensors["nvidia"]["displays"]
                    ]
                    if "displays" in windows_sensors["nvidia"]
                    and windows_sensors["nvidia"]["displays"] is not None
                    else [],
                    driver=SensorsNVIDIADriver(
                        branch_version=windows_sensors["nvidia"]["driver"][
                            "branch_version"
                        ],
                        interface_version=windows_sensors["nvidia"]["driver"][
                            "interface_version"
                        ],
                        version=windows_sensors["nvidia"]["driver"]["version"],
                    ),
                    gpus=[
                        SensorsNVIDIAGPU(
                            id=gpu["id"],
                            name=gpu["name"],
                            bios_oem_revision=gpu["bios_oem_revision"],
                            bios_revision=gpu["bios_revision"],
                            bios_version=gpu["bios_version"],
                            current_fan_speed_level=gpu["current_fan_speed_level"],
                            current_fan_speed_rpm=gpu["current_fan_speed_rpm"],
                            driver_model=gpu["driver_model"],
                            memory_available=gpu["memory_available"],
                            memory_capacity=gpu["memory_capacity"],
                            memory_maker=gpu["memory_maker"],
                            serial=gpu["serial"],
                            system_type=gpu["system_type"],
                            type=gpu["type"],
                        )
                        for gpu in windows_sensors["nvidia"]["gpus"]
                        if gpu is not None
                    ]
                    if "gpus" in windows_sensors["nvidia"]
                    and windows_sensors["nvidia"]["gpus"] is not None
                    else [],
                )
                if "nvidia" in windows_sensors and windows_sensors["nvidia"] is not None
                else None,
            )
            if windows_sensors is not None
            else None,
        )
