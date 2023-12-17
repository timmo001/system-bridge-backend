"""Sensors."""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys

import psutil
from systembridgemodels.sensors import (
    Sensors,
    SensorsWindows,
    SensorsWindowsHardware,
    SensorsWindowsSensor,
)

from .base import ModuleUpdateBase

# TODO: Fix sensors


class SensorsUpdate(ModuleUpdateBase):
    """Sensors Update."""

    async def _get_fans(self) -> dict | None:
        """Get fans."""
        if not hasattr(psutil, "sensors_fans"):
            return None
        return psutil.sensors_fans()  # type: ignore

    async def _get_temperatures(self) -> dict | None:
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
        except (ImportError, ModuleNotFoundError) as error:
            self._logger.error("Windows sensors not found", exc_info=error)
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
        except Exception as error:  # pylint: disable=broad-except
            self._logger.error(
                "Windows sensors error for path: %s", path, exc_info=error
            )
            return None

        try:
            return json.loads(result)
        except json.decoder.JSONDecodeError as error:
            self._logger.error("JSONDecodeError", exc_info=error)
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
                ],
            )
            if windows_sensors
            else None,
        )
