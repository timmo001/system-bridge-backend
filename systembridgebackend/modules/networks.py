"""Network."""

import asyncio
from typing import override

from psutil import net_connections, net_if_addrs, net_if_stats, net_io_counters
from psutil._common import sconn, snetio, snicaddr, snicstats

from systembridgemodels.modules.networks import (
    Network,
    NetworkAddress,
    NetworkConnection,
    NetworkIO,
    Networks,
    NetworkStats,
)

from .base import ModuleUpdateBase


class NetworksUpdate(ModuleUpdateBase):
    """Networks Update."""

    async def _get_addresses(
        self,
    ) -> dict[str, list[snicaddr]]:
        """Addresses."""
        return net_if_addrs()

    async def _get_connections(self) -> list[sconn]:
        """Get connections."""
        return net_connections("all")

    async def _get_io_counters(self) -> snetio:
        """IO Counters."""
        return net_io_counters()

    async def _get_stats(self) -> dict[str, snicstats]:
        """Stats."""
        return net_if_stats()

    @override
    async def update_all_data(self) -> Networks:
        """Update all data."""
        self._logger.debug("Update all data")

        (addresses, connections, io_counters, stats) = await asyncio.gather(
            *[
                self._get_addresses(),
                self._get_connections(),
                self._get_io_counters(),
                self._get_stats(),
            ]
        )

        networks: list[Network] = []

        for name, stat in stats.items():
            addrs = addresses.get(name, None)
            networks.append(
                Network(
                    name=name,
                    addresses=[
                        NetworkAddress(
                            address=address.address,
                            family=address.family,
                            netmask=address.netmask,
                            broadcast=address.broadcast,
                            ptp=address.ptp,
                        )
                        for address in addrs
                    ],
                    stats=NetworkStats(
                        isup=stat.isup,
                        duplex=stat.duplex,
                        speed=stat.speed,
                        mtu=stat.mtu,
                        flags=stat.flags,
                    ),
                )
            )

        return Networks(
            connections=[
                NetworkConnection(
                    fd=connection.fd,
                    family=connection.family,
                    laddr=connection.laddr,
                    raddr=connection.raddr,
                    status=connection.status,
                    type=connection.type,
                )
                for connection in connections
            ],
            io=NetworkIO(
                bytes_recv=io_counters.bytes_recv,
                bytes_sent=io_counters.bytes_sent,
                dropin=io_counters.dropin,
                dropout=io_counters.dropout,
                errin=io_counters.errin,
                errout=io_counters.errout,
                packets_recv=io_counters.packets_recv,
                packets_sent=io_counters.packets_sent,
            ),
            networks=networks,
        )
