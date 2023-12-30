"""Update Thread."""
import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from ..modules import Update
from . import BaseThread


class UpdateThread(BaseThread):
    """Update thread."""

    def __init__(
        self,
        updated_callback: Callable[[str, Any], Awaitable[None]],
    ) -> None:
        """Initialise."""
        super().__init__()
        self._update = Update(updated_callback)

    def run(self) -> None:
        """Run."""
        try:
            asyncio.run(self._update.update_data())
        except Exception as exception:  # pylint: disable=broad-except
            self._logger.exception(exception)
