"""System Bridge: Battery"""
from __future__ import annotations

from typing import override

from plyer import battery
from systembridgemodels.battery import Battery

from .base import ModuleUpdateBase


class BatteryUpdate(ModuleUpdateBase):
    """Battery Update"""

    @override
    async def update_all_data(self) -> Battery:
        """Update all data"""
        status = battery.status
        return Battery(
            is_charging=getattr(status, "isCharging", None),
            percentage=getattr(status, "percentage", None),
        )
