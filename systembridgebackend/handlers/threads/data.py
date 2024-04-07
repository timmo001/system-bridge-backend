"""Data update thread handler."""

from collections.abc import Awaitable, Callable
from typing import Any, Final, override

from ...modules import ModulesUpdate
from .update import UpdateThread

UPDATE_INTERVAL: Final[int] = 30


class DataUpdateThread(UpdateThread):
    """Data update thread."""

    def __init__(
        self,
        updated_callback: Callable[[str, Any], Awaitable[None]],
    ) -> None:
        """Initialise."""
        super().__init__(UPDATE_INTERVAL)
        self._update_cls = ModulesUpdate(updated_callback)

    @override
    async def update(self) -> None:
        """Update."""
        if self.stopping:
            return

        await self._update_cls.update_data()
