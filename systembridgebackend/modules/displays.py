"""Displays."""

from typing import NamedTuple, override

from monitorcontrol.monitorcontrol import get_monitors as vcp_get_monitors
from monitorcontrol.vcp import VCPCode
from monitorcontrol.vcp.vcp_abc import VCPError
from screeninfo import ScreenInfoError, get_monitors

from systembridgemodels.modules.displays import Display
from systembridgemodels.modules.sensors import Sensors

from .base import ModuleUpdateBase


class CustomVCPCode(VCPCode):
    """
    Subclass `VCPCode` to allow for custom VCP code definitions.

    Args:
        definition (dict): A dictionary containing the following keys:
            - name (str): The name of the VCP code.
            - value (int): The value of the VCP code. usually a hexadecimal value.
            - type (str): The type of the VCP code. Can be "rw" (read-write) or "ro" (read-only).
            - function (str): The function of the VCP code. Can be "c" (Continuous), or "nc" (Non-continuous).
    """
    def __init__(self, definition: dict):  # pylint: disable=super-init-not-called
        self.definition = definition


class VCPMonitorInfo(NamedTuple):
    """
    A named tuple to hold monitor information.
    """
    vcp_supported: bool
    brightness: int = None
    contrast: int = None
    volume: int = None
    power_state: int = None
    input_source: int = None


vcpcode_volume = CustomVCPCode({
    "name": "audio speaker volume",
    "value": 0x62,
    "type": "rw",
    "function": "c",
})


class DisplaysUpdate(ModuleUpdateBase):
    """Displays Update."""

    def __init__(self) -> None:
        """Initialise."""
        super().__init__()
        self.sensors: Sensors | None = None
        self.vcp_monitor_blacklist = set()

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

    def sensors_vcp_info(
        self,
        index: int,
        name: str,
    ) -> VCPMonitorInfo:
        """Get VCP info for a specific monitor."""
        if name not in self.vcp_monitor_blacklist:
            vcp_monitors = vcp_get_monitors()
            try:
                def permissive(lambda_func):
                    try: return lambda_func()
                    except VCPError: pass

                vcp_monitor = vcp_monitors[index]
                with vcp_monitor:
                    brightness = vcp_monitor.get_luminance()
                    contrast = permissive(vcp_monitor.get_contrast)
                    volume = permissive(lambda: vcp_monitor._get_vcp_feature(vcpcode_volume))  # pylint: disable=protected-access
                    power_state = permissive(lambda: vcp_monitor.get_power_mode().value)
                    input_source = permissive(lambda: vcp_monitor.get_input_source().value)

                    return VCPMonitorInfo(True, brightness, contrast, volume, power_state, input_source)
            except VCPError as e:
                self._logger.error("Error querying Monitor %d %s through VCP: %s", index, name, str(e))
                self.vcp_monitor_blacklist.add(name)
                return VCPMonitorInfo(False)
        else:
            self._logger.info("Skipped VCP query for blacklisted monitor %d %s", index, name)
            return VCPMonitorInfo(False)

    @override
    async def update_all_data(self) -> list[Display]:
        """Update all data."""
        self._logger.debug("Update all data")

        try:
            monitors = []
            for key, monitor in enumerate(get_monitors()):
                vcp_info = self.sensors_vcp_info(key, monitor.name)
                monitors.append(Display(
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
                    vcp_supported=vcp_info.vcp_supported,
                    brightness=vcp_info.brightness,
                    contrast=vcp_info.contrast,
                    volume=vcp_info.volume,
                    power_state=vcp_info.power_state,
                    input_source=vcp_info.input_source,
                    sdr_white_level=None,
                ))
            return monitors
        except ScreenInfoError as error:
            self._logger.error(error)
            return []
