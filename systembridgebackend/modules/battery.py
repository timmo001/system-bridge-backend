"""Battery."""

from typing import override

from plyer import battery
import psutil

from systembridgemodels.modules.battery import Battery

from .base import ModuleUpdateBase


class BatteryUpdate(ModuleUpdateBase):
    """Battery Update."""

    def _get_sensors(self) -> psutil._common.sbattery | None:  # type: ignore
        """Get battery sensors."""
        if not hasattr(psutil, "sensors_battery"):
            return None
        return psutil.sensors_battery()  # type: ignore

    @override
    async def update_all_data(self) -> Battery:
        """Update all data."""
        self._logger.debug("Update all data")

        sensors = self._get_sensors()
        time_remaining = (
            sensors.secsleft
            if sensors is not None and hasattr(sensors, "secsleft")
            else None
        )

        try:
            status = battery.status
            if (status) is None or (
                status["percentage"] == 255 and status["isCharging"] is False
            ):
                return Battery(
                    is_charging=None,
                    percentage=None,
                    time_remaining=time_remaining,
                )
            return Battery(
                is_charging=status["isCharging"],
                percentage=status["percentage"],
                time_remaining=time_remaining,
            )
        except ValueError as exception:
            self._logger.error(exception)
            return Battery(
                is_charging=None,
                percentage=None,
                time_remaining=time_remaining,
            )
