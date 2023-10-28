"""System Bridge"""
from __future__ import annotations

import asyncio
import os
import sys

from systembridgeshared.base import Base
from systembridgeshared.const import SECRET_API_KEY, SETTING_AUTOSTART
from systembridgeshared.database import Database
from systembridgeshared.settings import Settings

from .modules.listeners import Listeners
from .modules.system import System
from .server import Server
from .utilities.autostart import autostart_disable, autostart_enable


class Application(Base):
    """Application"""

    def __init__(
        self,
        database: Database,
        settings: Settings,
        cli: bool = False,
        init: bool = False,
        no_frontend: bool = False,
        no_gui: bool = False,
    ) -> None:
        """Initialize"""
        super().__init__()
        if init:
            self._logger.info("Initialized application. Exiting now.")
            sys.exit(0)

        self._logger.info("System Bridge %s: Startup", System().version())

        self._logger.info(
            "Your api-key is: %s",
            str(settings.get_secret(SECRET_API_KEY)),
        )

        if not cli:
            autostart = settings.get(SETTING_AUTOSTART)
            self._logger.info("Autostart enabled: %s", autostart)
            if autostart:
                autostart_enable()
            else:
                autostart_disable()

        listeners = Listeners(database)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        self._server = Server(
            database,
            settings,
            listeners,
            no_frontend=no_frontend,
            no_gui=no_gui,
        )
        loop.run_until_complete(self._server.start())
