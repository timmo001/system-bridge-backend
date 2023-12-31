"""System Bridge: Server."""
import asyncio
from collections.abc import Callable
import sys

import uvicorn

from systembridgemodels.action import Action
from systembridgemodels.settings import SettingHotkey
from systembridgeshared.base import Base
from systembridgeshared.settings import Settings

from ..handlers.action import ActionHandler
from ..handlers.data import DataUpdate
from ..handlers.gui import GUI, GUICommand
from ..handlers.keyboard import keyboard_hotkey_register
from ..modules.listeners import Listeners
from ..server.mdns import MDNSAdvertisement
from .api import app as api_app


class APIServer(uvicorn.Server):
    """Customized uvicorn.Server.

    Uvicorn server overrides signals and we need to include
    Tasks to the signals.
    """

    def __init__(
        self,
        config: uvicorn.Config,
        exit_callback: Callable[[], None],
    ) -> None:
        """Initialise."""
        super().__init__(config)
        self._exit_callback = exit_callback

    def handle_exit(self, sig: int, frame) -> None:
        """Handle exit."""
        self._exit_callback()
        return super().handle_exit(sig, frame)


class Server(Base):
    """Server."""

    def __init__(
        self,
        settings: Settings,
        listeners: Listeners,
        no_frontend: bool = False,
        no_gui: bool = False,
    ) -> None:
        """Initialise."""
        super().__init__()
        self.no_frontend = no_frontend
        self.no_gui = no_gui

        self._listeners = listeners
        self._settings = settings
        self._tasks: list[asyncio.Task] = []

        self._gui_main: GUI | None = None
        self._gui_notification: GUI | None = None
        self._gui_player: GUI | None = None

        self._mdns_advertisement = MDNSAdvertisement(settings)
        self._mdns_advertisement.advertise_server()

        self._logger.info("Setup API app")
        api_app.callback_exit = self.exit_application
        api_app.callback_open_gui = self.open_gui
        api_app.data_update = DataUpdate(self.data_updated)
        api_app.listeners = listeners
        api_app.loop = asyncio.get_event_loop()

        self._logger.info("Setup API server")
        self._api_server = APIServer(
            config=uvicorn.Config(
                api_app,
                host="0.0.0.0",
                loop="asyncio",
                log_config=None,
                log_level=settings.data.log_level.lower(),
                port=settings.data.api.port,
                workers=8,
            ),
            exit_callback=self.exit_application,
        )
        self._logger.info("Server initialised")

    async def start(self) -> None:
        """Start the server."""
        self._logger.info("Start server")
        self._tasks.extend(
            [
                api_app.loop.create_task(
                    self._api_server.serve(),
                    name="API",
                ),
                api_app.loop.create_task(
                    self.register_hotkeys(),
                    name="Hotkeys",
                ),
            ]
        )

        # Start update threads
        api_app.data_update.request_update_data()
        api_app.data_update.request_update_media_data()

        # Start the GUI
        if not self.no_gui:
            self.open_gui(GUICommand.MAIN, "")

        await asyncio.wait(self._tasks)

    async def data_updated(
        self,
        module: str,
    ) -> None:
        """Update data."""
        await self._listeners.refresh_data_by_module(
            api_app.data_update.data,
            module,
        )

    def open_gui(
        self,
        command: GUICommand,
        data: str,
    ) -> None:
        """Open GUI."""
        if command == GUICommand.MAIN:
            self._logger.info("Launch Main GUI as a detached process")
            if self._gui_main is not None:
                self._gui_main.stop()
            self._gui_main = GUI(self._settings)
            self._tasks.append(
                api_app.loop.create_task(
                    self._gui_main.start(
                        self.exit_application,
                        command,
                        data,
                    ),
                    name="GUI Main",
                )
            )
        elif command == GUICommand.NOTIFICATION:
            self._logger.info("Launch Notification GUI as a detached process")
            if self._gui_notification is not None:
                self._gui_notification.stop()
            self._gui_notification = GUI(self._settings)
            self._tasks.append(
                api_app.loop.create_task(
                    self._gui_notification.start(
                        self.exit_application,
                        command,
                        data,
                    ),
                    name="GUI Notification",
                )
            )
        elif command == GUICommand.PLAYER:
            self._logger.info("Launch Player GUI as a detached process")
            if self._gui_player:
                self._gui_player.stop()
            self._gui_player = GUI(self._settings)
            self._tasks.append(
                api_app.loop.create_task(
                    self._gui_player.start(
                        self.exit_application,
                        command,
                        data,
                    ),
                    name="GUI Media Player",
                )
            )
        else:
            raise NotImplementedError(f"Command not implemented: {command}")

    def exit_application(self) -> None:
        """Exit application."""
        self._logger.info("Exiting application")

        # Stop update threads
        if api_app.data_update.update_data_thread is not None:
            api_app.data_update.update_data_thread.join()
        if api_app.data_update.update_media_thread is not None:
            api_app.data_update.update_media_thread.join()
        self._logger.info("Update threads joined")

        # Stop all tasks
        for task in self._tasks:
            task.cancel()
        self._logger.info("Tasks cancelled")

        # Stop the API server
        self._logger.info("Stop API server")
        self._api_server.should_exit = True
        self._api_server.force_exit = True
        self._logger.info("API server stopped")

        # Stop GUI threads
        if self._gui_main is not None:
            self._gui_main.stop()
        if self._gui_notification is not None:
            self._gui_notification.stop()
        if self._gui_player is not None:
            self._gui_player.stop()
        self._logger.info("GUI threads joined")

        # Stop the event loop
        loop = asyncio.get_event_loop()
        asyncio.tasks.all_tasks(loop).clear()
        self._logger.info("Tasks cleared")
        loop.stop()
        self._logger.info("Event loop stopped")

        self._logger.info("Exit Application")
        sys.exit(0)

    async def register_hotkeys(self) -> None:
        """Register hotkeys."""
        self._logger.info("Register hotkeys")
        hotkeys = self._settings.data.keyboard_hotkeys
        if hotkeys is not None and isinstance(hotkeys, list):
            self._logger.info("Found %s hotkeys", len(hotkeys))
            for item in hotkeys:
                self.register_hotkey(item)

    def register_hotkey(
        self,
        hotkey: SettingHotkey,
    ) -> None:
        """Register hotkey."""
        self._logger.info("Register hotkey: %s", hotkey)

        def hotkey_callback() -> None:
            """Hotkey callback."""
            self._logger.info("Hotkey pressed: %s", hotkey)
            action_handler = ActionHandler(self._settings)
            api_app.loop.create_task(action_handler.handle(Action(hotkey.key)))

        keyboard_hotkey_register(
            hotkey.key,
            hotkey_callback,
        )
