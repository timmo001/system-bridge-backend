"""System Bridge: Modules Base"""

from systembridgeshared.base import Base


class ModuleUpdateBase(Base):
    """Module Base"""

    async def update_all_data(self) -> None:
        """Update data"""
        raise NotImplementedError()
