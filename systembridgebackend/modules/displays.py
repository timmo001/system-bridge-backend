"""Displays."""

from typing import override

from screeninfo import ScreenInfoError, get_monitors

from systembridgemodels.modules.displays import Display
from systembridgemodels.modules.sensors import Sensors

from .base import ModuleUpdateBase


class DisplaysUpdate(ModuleUpdateBase):
    """Displays Update."""

    def __init__(self) -> None:
        """Initialise."""
        super().__init__()
        self.sensors: Sensors | None = None

    def _get_pixel_clock(
        self,
        display_key: str,
    ) -> float | None:
        """Display pixel clock."""
        if (
            self.sensors is None
            or self.sensors.windows_sensors is None
            or self.sensors.windows_sensors.hardware is None
        ):
            return None
        for hardware in self.sensors.windows_sensors.hardware:
            # Find type "DISPLAY" and name display_key
            if (
                "DISPLAY" not in hardware.type.upper()
                and display_key not in hardware.name.upper()
            ):
                continue
            for sensor in hardware.sensors:
                name = sensor.name.upper()
                # Find name "PIXEL" and "CLOCK"
                if "PIXEL" not in name or "CLOCK" not in name:
                    continue
                self._logger.debug(
                    "Found display pixel clock: %s = %s",
                    sensor.name,
                    sensor.value,
                )
                return int(sensor.value) if sensor.value is not None else None
        return None

    def sensors_refresh_rate(
        self,
        display_key: str,
    ) -> float | None:
        """Display refresh rate."""
        if (
            self.sensors is None
            or self.sensors.windows_sensors is None
            or self.sensors.windows_sensors.hardware is None
        ):
            return None
        for hardware in self.sensors.windows_sensors.hardware:
            # Find type "DISPLAY" and name display_key
            if (
                "DISPLAY" not in hardware.type.upper()
                and display_key not in hardware.name.upper()
            ):
                continue
            for sensor in hardware.sensors:
                name = sensor.name.upper()
                # Find name "REFRESH" and "RATE"
                if "REFRESH" not in name or "RATE" not in name:
                    continue
                self._logger.debug(
                    "Found display refresh rate: %s = %s",
                    sensor.name,
                    sensor.value,
                )
                return int(sensor.value) if sensor.value is not None else None
        return None

    def sensors_resolution_horizontal(
        self,
        display_key: str,
    ) -> int | None:
        """Display resolution horizontal."""
        if (
            self.sensors is None
            or self.sensors.windows_sensors is None
            or self.sensors.windows_sensors.hardware is None
        ):
            return None
        for hardware in self.sensors.windows_sensors.hardware:
            # Find type "DISPLAY" and name display_key
            if (
                "DISPLAY" not in hardware.type.upper()
                and display_key not in hardware.name.upper()
            ):
                continue
            for sensor in hardware.sensors:
                name = sensor.name.upper()
                # Find name "RESOLUTION" and "HORIZONTAL"
                if "RESOLUTION" not in name or "HORIZONTAL" not in name:
                    continue
                self._logger.debug(
                    "Found display resolution horizontal: %s = %s",
                    sensor.name,
                    sensor.value,
                )
                return int(sensor.value) if sensor.value is not None else None
        return None

    def sensors_resolution_vertical(
        self,
        display_key: str,
    ) -> int | None:
        """Display resolution vertical."""
        if (
            self.sensors is None
            or self.sensors.windows_sensors is None
            or self.sensors.windows_sensors.hardware is None
        ):
            return None
        for hardware in self.sensors.windows_sensors.hardware:
            # Find type "DISPLAY" and name display_key
            if (
                "DISPLAY" not in hardware.type.upper()
                and display_key not in hardware.name.upper()
            ):
                continue
            for sensor in hardware.sensors:
                name = sensor.name.upper()
                # Find name "RESOLUTION" and "VERTICAL"
                if "RESOLUTION" not in name or "VERTICAL" not in name:
                    continue
                self._logger.debug(
                    "Found display resolution vertical: %s = %s",
                    sensor.name,
                    sensor.value,
                )
                return int(sensor.value) if sensor.value is not None else None
        return None

    @override
    async def update_all_data(self) -> list[Display]:
        """Update all data."""
        self._logger.debug("Update all data")

        try:
            return [
                Display(
                    id=str(key),
                    name=monitor.name if monitor.name is not None else str(key),
                    resolution_horizontal=monitor.width,
                    resolution_vertical=monitor.height,
                    x=monitor.x,
                    y=monitor.y,
                    width=monitor.width_mm,
                    height=monitor.height_mm,
                    is_primary=monitor.is_primary,
                    pixel_clock=self._get_pixel_clock(str(key)),
                    refresh_rate=self.sensors_refresh_rate(str(key)),
                )
                for key, monitor in enumerate(get_monitors())
            ]
        except ScreenInfoError as error:
            self._logger.error(error)
            return []
