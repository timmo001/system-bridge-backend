"""System Bridge: Remote Bridge Utilities"""
from systembridgemodels.database_data_remote_bridge import RemoteBridge
from systembridgeshared.database import Database


def get_remote_bridges(
    database: Database,
) -> list[RemoteBridge]:
    """Get all remote bridges."""
    return database.get_data(RemoteBridge)
