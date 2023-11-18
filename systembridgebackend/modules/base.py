"""System Bridge: Modules Base"""

from typing import Any

from systembridgeshared.base import Base
from systembridgeshared.database import Database


class ModuleUpdateBase(Base):
    """Module Base"""

    def __init__(
        self,
        database: Database,
        model:Any,
    ):
        super().__init__()

        self._database = database

        # Clear table on init
        self._database.clear_table(model)

    async def update_all_data(self) -> None:
        """Update data"""
        raise NotImplementedError()
