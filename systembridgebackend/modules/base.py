"""Modules Base."""

from typing import Any

from systembridgeshared.base import Base


class ModuleUpdateBase(Base):
    """Module Base."""

    data: Any | None = None

    async def update_all_data(self) -> Any:
        """Update data."""
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement update_all_data"
        )
