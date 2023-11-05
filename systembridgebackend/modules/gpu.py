"""System Bridge: GPU"""
from __future__ import annotations

import asyncio
from json import dumps
from typing import Optional

from systembridgeshared.base import Base
from systembridgeshared.common import make_key
from systembridgeshared.database import Database
from systembridgeshared.models.database_data import GPU as DatabaseModel
from systembridgeshared.models.database_data_sensors import (
    Sensors as SensorsDatabaseModel,
)

from .base import ModuleUpdateBase


class GPU(Base):
    """GPU"""

    def get_gpus(
        self,
        database: Database,
    ) -> list[str]:
        """Get GPUs"""
        gpus = []
        for item in database.get_data(SensorsDatabaseModel):
            if (
                item.hardware_type is not None
                and "gpu" in item.hardware_type.lower()
                and item.hardware_name not in gpus
            ):
                gpus.append(item.hardware_name)
        return gpus

    def core_clock(
        self,
        database: Database,
        gpu_key: str,
    ) -> Optional[float]:
        """GPU core clock"""
        for item in database.get_data(SensorsDatabaseModel):
            if (
                item.hardware_type is not None
                and "gpu" in item.hardware_type.lower()
                and "clock" in item.type.lower()
                and "core" in item.name.lower()
                and make_key(item.hardware_name) == gpu_key
            ):
                self._logger.debug(
                    "Found GPU core clock: %s = %s",
                    item.key,
                    item.value,
                )
                return item.value
        return None

    def core_load(
        self,
        database: Database,
        gpu_key: str,
    ) -> Optional[float]:
        """GPU core load"""
        for item in database.get_data(SensorsDatabaseModel):
            if (
                item.hardware_type is not None
                and "gpu" in item.hardware_type.lower()
                and "load" in item.type.lower()
                and "core" in item.name.lower()
                and make_key(item.hardware_name) == gpu_key
            ):
                self._logger.debug("Found GPU core load: %s = %s", item.key, item.value)
                return item.value
        return None

    def fan_speed(
        self,
        database: Database,
        gpu_key: str,
    ) -> Optional[float]:
        """GPU fan speed"""
        for item in database.get_data(SensorsDatabaseModel):
            if (
                item.hardware_type is not None
                and "gpu" in item.hardware_type.lower()
                and "fan" in item.type.lower()
                and make_key(item.hardware_name) == gpu_key
            ):
                self._logger.debug("Found GPU fan speed: %s = %s", item.key, item.value)
                return item.value
        return None

    def memory_clock(
        self,
        database: Database,
        gpu_key: str,
    ) -> Optional[float]:
        """GPU memory clock"""
        for item in database.get_data(SensorsDatabaseModel):
            if (
                item.hardware_type is not None
                and "gpu" in item.hardware_type.lower()
                and "clock" in item.type.lower()
                and "memory" in item.name.lower()
                and make_key(item.hardware_name) == gpu_key
            ):
                self._logger.debug(
                    "Found GPU memory clock: %s = %s",
                    item.key,
                    item.value,
                )
                return item.value
        return None

    def memory_load(
        self,
        database: Database,
        gpu_key: str,
    ) -> Optional[float]:
        """GPU memory load"""
        for item in database.get_data(SensorsDatabaseModel):
            if (
                item.hardware_type is not None
                and "gpu" in item.hardware_type.lower()
                and "load" in item.type.lower()
                and "memory" in item.name.lower()
                and make_key(item.hardware_name) == gpu_key
            ):
                self._logger.debug(
                    "Found GPU memory load: %s = %s",
                    item.key,
                    item.value,
                )
                return item.value
        return None

    def memory_free(
        self,
        database: Database,
        gpu_key: str,
    ) -> Optional[float]:
        """GPU memory free"""
        for item in database.get_data(SensorsDatabaseModel):
            if (
                item.hardware_type is not None
                and "gpu" in item.hardware_type.lower()
                and "memory" in item.name.lower()
                and "free" in item.name.lower()
                and make_key(item.hardware_name) == gpu_key
            ):
                self._logger.debug(
                    "Found GPU memory free: %s = %s",
                    item.key,
                    item.value,
                )
                return item.value
        return None

    def memory_used(
        self,
        database: Database,
        gpu_key: str,
    ) -> Optional[float]:
        """GPU memory used"""
        for item in database.get_data(SensorsDatabaseModel):
            if (
                item.hardware_type is not None
                and "gpu" in item.hardware_type.lower()
                and "memory" in item.name.lower()
                and "used" in item.name.lower()
                and make_key(item.hardware_name) == gpu_key
            ):
                self._logger.debug(
                    "Found GPU memory used: %s = %s",
                    item.key,
                    item.value,
                )
                return item.value
        return None

    def memory_total(
        self,
        database: Database,
        gpu_key: str,
    ) -> Optional[float]:
        """GPU memory total"""
        for item in database.get_data(SensorsDatabaseModel):
            if (
                item.hardware_type is not None
                and "gpu" in item.hardware_type.lower()
                and "memory" in item.name.lower()
                and "total" in item.name.lower()
                and make_key(item.hardware_name) == gpu_key
            ):
                self._logger.debug(
                    "Found GPU memory total: %s = %s",
                    item.key,
                    item.value,
                )
                return item.value
        return None

    def power(
        self,
        database: Database,
        gpu_key: str,
    ) -> Optional[float]:
        """GPU power usage"""
        for item in database.get_data(SensorsDatabaseModel):
            if (
                item.hardware_type is not None
                and "gpu" in item.hardware_type.lower()
                and "power" in item.type.lower()
                and make_key(item.hardware_name) == gpu_key
            ):
                self._logger.debug("Found GPU power: %s = %s", item.key, item.value)
                return item.value
        return None

    def temperature(
        self,
        database: Database,
        gpu_key: str,
    ) -> Optional[float]:
        """GPU temperature"""
        for item in database.get_data(SensorsDatabaseModel):
            if (
                item.hardware_type is not None
                and "gpu" in item.hardware_type.lower()
                and "temperature" in item.type.lower()
                and "core" in item.name.lower()
                and make_key(item.hardware_name) == gpu_key
            ):
                self._logger.debug(
                    "Found GPU temperature: %s = %s",
                    item.key,
                    item.value,
                )
                return item.value
        return None


class GPUUpdate(ModuleUpdateBase):
    """GPU Update"""

    def __init__(
        self,
        database: Database,
    ) -> None:
        """Initialize"""
        super().__init__(database)
        self._gpu = GPU()

    async def update_name(
        self,
        gpu_key: str,
        gpu_name: str,
    ) -> None:
        """Update name"""
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key=f"{gpu_key}_name",
                value=gpu_name,
            ),
        )

    async def update_core_clock(
        self,
        gpu_key: str,
    ) -> None:
        """Update core clock"""
        value = self._gpu.core_clock(self._database, gpu_key)
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key=f"{gpu_key}_core_clock",
                value=str(value) if value else None,
            ),
        )

    async def update_core_load(
        self,
        gpu_key: str,
    ) -> None:
        """Update core load"""
        value = self._gpu.core_load(self._database, gpu_key)
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key=f"{gpu_key}_core_load",
                value=str(value) if value else None,
            ),
        )

    async def update_fan_speed(
        self,
        gpu_key: str,
    ) -> None:
        """Update fan speed"""
        value = self._gpu.fan_speed(self._database, gpu_key)
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key=f"{gpu_key}_fan_speed",
                value=str(value) if value else None,
            ),
        )

    async def update_memory_clock(
        self,
        gpu_key: str,
    ) -> None:
        """Update memory clock"""
        value = self._gpu.memory_clock(self._database, gpu_key)
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key=f"{gpu_key}_memory_clock",
                value=str(value) if value else None,
            ),
        )

    async def update_memory_load(
        self,
        gpu_key: str,
    ) -> None:
        """Update memory load"""
        value = self._gpu.memory_load(self._database, gpu_key)
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key=f"{gpu_key}_memory_load",
                value=str(value) if value else None,
            ),
        )

    async def update_memory_free(
        self,
        gpu_key: str,
    ) -> None:
        """Update memory free"""
        value = self._gpu.memory_free(self._database, gpu_key)
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key=f"{gpu_key}_memory_free",
                value=str(value) if value else None,
            ),
        )

    async def update_memory_used(
        self,
        gpu_key: str,
    ) -> None:
        """Update memory used"""
        value = self._gpu.memory_used(self._database, gpu_key)
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key=f"{gpu_key}_memory_used",
                value=str(value) if value else None,
            ),
        )

    async def update_memory_total(
        self,
        gpu_key: str,
    ) -> None:
        """Update memory total"""
        value = self._gpu.memory_total(self._database, gpu_key)
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key=f"{gpu_key}_memory_total",
                value=str(value) if value else None,
            ),
        )

    async def update_power(
        self,
        gpu_key: str,
    ) -> None:
        """Update power"""
        value = self._gpu.power(self._database, gpu_key)
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key=f"{gpu_key}_power",
                value=str(value) if value else None,
            ),
        )

    async def update_temperature(
        self,
        gpu_key: str,
    ) -> None:
        """Update temperature"""
        value = self._gpu.temperature(self._database, gpu_key)
        self._database.update_data(
            DatabaseModel,
            DatabaseModel(
                key=f"{gpu_key}_temperature",
                value=str(value) if value else None,
            ),
        )

    async def update_all_data(self) -> None:
        """Update data"""
        gpu_list = []
        gpus = self._gpu.get_gpus(self._database)

        if gpus is not None and len(gpus) > 0:
            # Clear table in case of hardware changes since last run
            self._database.clear_table(DatabaseModel)
            for gpu_name in gpus:
                gpu_key = make_key(gpu_name)
                gpu_list.append(gpu_key)
                await asyncio.gather(
                    *[
                        self.update_name(gpu_key, gpu_name),
                        self.update_core_clock(gpu_key),
                        self.update_core_load(gpu_key),
                        self.update_fan_speed(gpu_key),
                        self.update_memory_clock(gpu_key),
                        self.update_memory_load(gpu_key),
                        self.update_memory_free(gpu_key),
                        self.update_memory_used(gpu_key),
                        self.update_memory_total(gpu_key),
                        self.update_power(gpu_key),
                        self.update_temperature(gpu_key),
                    ]
                )
            self._database.update_data(
                DatabaseModel,
                DatabaseModel(
                    key="gpus",
                    value=dumps(gpu_list),
                ),
            )
