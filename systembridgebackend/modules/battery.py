"""Battery."""
from __future__ import annotations

from typing import override

from plyer import battery

from systembridgemodels.modules.battery import Battery

from .base import ModuleUpdateBase


class BatteryUpdate(ModuleUpdateBase):
    """Battery Update."""

    @override
    async def update_all_data(self) -> Battery:
        """Update all data."""
        self._logger.debug("Update all data")

        status = battery.status
        if (status) is None or (
            status["percentage"] == 255 and status["isCharging"] is False
        ):
            return Battery(
                is_charging=None,
                percentage=None,
            )
        return Battery(
            is_charging=status["isCharging"],
            percentage=status["percentage"],
        )
