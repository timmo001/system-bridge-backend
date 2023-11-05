"""System Bridge: Network"""
import asyncio

from psutil import net_connections, net_if_addrs, net_if_stats, net_io_counters
from psutil._common import sconn, snetio, snicaddr, snicstats
from systembridgeshared.base import Base
from systembridgeshared.database import Database
from systembridgeshared.models.database_data import Network as DatabaseModel

from .base import ModuleUpdateBase


class Network(Base):
    """Network"""

    def connections(self) -> list[sconn]:  # pylint: disable=unsubscriptable-object
        """Connections"""
        return net_connections("all")

    def addresses(
        self,
    ) -> dict[str, list[snicaddr]]:  # pylint: disable=unsubscriptable-object
        """Addresses"""
        return net_if_addrs()

    def stats(self) -> dict[str, snicstats]:  # pylint: disable=unsubscriptable-object
        """Stats"""
        return net_if_stats()

    def io_counters(self) -> snetio:  # pylint: disable=unsubscriptable-object
        """IO Counters"""
        return net_io_counters()


class NetworkUpdate(ModuleUpdateBase):
    """Network Update"""

    def __init__(
        self,
        database: Database,
    ) -> None:
        """Initialize"""
        super().__init__(database)
        self._network = Network()

    async def update_stats(self) -> None:
        """Update stats"""
        for key, value in self._network.stats().items():
            for subkey, subvalue in value._asdict().items():
                self._database.update_data(
                    DatabaseModel,
                    DatabaseModel(
                        key=f"stat_{key.replace(' ', '')}_{subkey}",
                        value=subvalue,
                    ),
                )

    async def update_io_counters(self) -> None:
        """Update IO counters"""
        for key, value in self._network.io_counters()._asdict().items():
            self._database.update_data(
                DatabaseModel,
                DatabaseModel(
                    key=f"io_counters_{key}",
                    value=value,
                ),
            )

    async def update_all_data(self) -> None:
        """Update data"""
        await asyncio.gather(
            *[
                self.update_stats(),
                self.update_io_counters(),
            ]
        )
