"""Media update thread handler."""

from collections.abc import Awaitable, Callable
import datetime
import platform
from typing import Final, override

from systembridgemodels.modules.media import Media as MediaInfo

from .update import UpdateThread

UPDATE_INTERVAL: Final[int] = 20


class MediaUpdateThread(UpdateThread):
    """Media update thread."""

    def __init__(
        self,
        updated_callback: Callable[[str, MediaInfo], Awaitable[None]],
    ) -> None:
        """Initialise."""
        super().__init__(UPDATE_INTERVAL)
        self._updated_callback = updated_callback

        if platform.system() != "Windows":
            return

        from ...modules.media import (  # pylint: disable=import-outside-toplevel, import-error
            Media,  # pylint: disable=import-outside-toplevel, import-error
        )

        self._update_cls = Media(
            changed_callback=self._updated_callback,
            update_media_info_interval=self._update_interval,
        )

    @override
    async def update(self) -> None:
        """Update."""
        if self.stopping:
            return

        if platform.system() != "Windows" or self._update_cls is None:
            await self._updated_callback(
                "media", MediaInfo(updated_at=datetime.datetime.now().timestamp())
            )
            return

        await self._update_cls.update_media_info()
