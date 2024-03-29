"""Modules Listeners."""

from collections.abc import Awaitable, Callable

from systembridgemodels.modules import ModulesData
from systembridgemodels.response import Response
from systembridgeshared.base import Base

from . import MODULES


class Listener:
    """Listener."""

    def __init__(
        self,
        listener_id: str,
        send_response: Callable[[Response], None],
        data_changed_callback: Callable[[str, ModulesData], Awaitable[None]],
        modules: list[str],
    ) -> None:
        """Initialise."""
        self.id = listener_id
        self.send_response = send_response
        self.data_changed_callback = data_changed_callback
        self.modules = modules


class Listeners(Base):
    """Module Listeners."""

    def __init__(self) -> None:
        """Initialise."""
        super().__init__()
        self.registered_listeners: list[Listener] = []

    async def add_listener(
        self,
        listener_id: str,
        send_response: Callable[[dict[str, str]], None],
        data_changed_callback: Callable[[str, ModulesData], Awaitable[None]],
        modules: list[str],
    ) -> bool:
        """Add modules to listener."""
        for listner in self.registered_listeners:
            if listner.id == listener_id:
                self._logger.warning("Listener already registered: %s", listener_id)
                return True

        self.registered_listeners.append(
            Listener(listener_id, send_response, data_changed_callback, modules)
        )
        self._logger.info("Added listener: %s", listener_id)

        return False

    async def refresh_data_by_module(
        self,
        data: ModulesData,
        module: str,
    ) -> None:
        """Refresh data by module."""
        self._logger.info("Refresh data by module: %s", module)
        if module not in MODULES:
            self._logger.warning("Module to refresh not implemented: %s", module)
            return

        for listener in self.registered_listeners:
            self._logger.info("Listener: %s - %s", listener.id, listener.modules)
            if module in listener.modules:
                self._logger.info(
                    "Sending '%s' data to listener: %s", module, listener.id
                )
                await listener.data_changed_callback(module, data)

    def remove_all_listeners(self) -> None:
        """Remove all listeners."""
        self.registered_listeners.clear()

    def remove_listener(
        self,
        listener_id: str,
    ) -> bool:
        """Remove listener."""
        for listener in self.registered_listeners:
            if listener.id == listener_id:
                self.registered_listeners.remove(listener)
                self._logger.info("Removed listener: %s", listener_id)
                return True

        self._logger.info("Listener not found: %s", listener_id)
        return False
