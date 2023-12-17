"""System Bridge."""
from __future__ import annotations

import asyncio
import sys

from systembridgeshared.base import Base
from systembridgeshared.settings import Settings

from ._version import __version__
from .modules.listeners import Listeners
from .server import Server


class Application(Base):
    """Application."""

    def __init__(
        self,
        settings: Settings,
        init: bool = False,
        no_frontend: bool = False,
    ) -> None:
        """Initialise."""
        super().__init__()
        if init:
            self._logger.info("Initialised application. Exiting now.")
            sys.exit(0)

        self._logger.info("System Bridge %s: Startup", __version__.public())

        self._logger.info("Your token is: %s", settings.data.api.token)

        listeners = Listeners()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        self._server = Server(
            settings,
            listeners,
            no_frontend=no_frontend,
        )
        loop.run_until_complete(self._server.start())
