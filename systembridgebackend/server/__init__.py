"""System Bridge: Server."""
import asyncio
from collections.abc import Callable
import sys

from systembridgemodels.action import Action
from systembridgemodels.settings import SettingHotkey
from systembridgeshared.base import Base
from systembridgeshared.settings import Settings
import uvicorn

from ..data import DataUpdate
from ..gui import GUI
from ..modules.listeners import Listeners
from ..server.mdns import MDNSAdvertisement
from ..utilities.action import ActionHandler
from ..utilities.keyboard import keyboard_hotkey_register
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
    ) -> None:
        """Initialise."""
        super().__init__()
        self.no_frontend = no_frontend

        self._listeners = listeners
        self._settings = settings
        self._tasks: list[asyncio.Task] = []

        self._gui_notification: GUI | None = None
        self._gui_player: GUI | None = None

        self._mdns_advertisement = MDNSAdvertisement(settings)
        self._mdns_advertisement.advertise_server()

        self._logger.info("Setup API app")
        api_app.callback_exit = self.exit_application
        api_app.callback_open_gui = self.callback_open_gui
        api_app.data_update = DataUpdate(self.data_updated_callback)
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
                workers=4,
            ),
            exit_callback=self.exit_application,
        )
        self._logger.info("Server Initialised")

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
                    self.indefinite_func_wrapper(self.update_data),
                    name="Update data",
                ),
                api_app.loop.create_task(
                    self.indefinite_func_wrapper(self.update_media_data),
                    name="Update media data",
                ),
            ]
        )

        await asyncio.wait(self._tasks)

    async def data_updated_callback(
        self,
        module: str,
    ) -> None:
        """Update data."""
        await self._listeners.refresh_data_by_module(
            api_app.data_update.data,
            module,
        )

    def callback_open_gui(
        self,
        command: str,
        data: str,
    ) -> None:
        """Open GUI."""
        if command == "notification":
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
        elif command == "player":
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

    async def indefinite_func_wrapper(self, func) -> None:
        """Indefinite function wrapper."""
        while not self._api_server.should_exit:
            await func()
        self._logger.info(
            "Indefinite function wrapper exited for: %s",
            func.__name__,
        )

    def exit_application(self) -> None:
        """Exit application."""
        self._logger.info("Exiting application")

        # Stop the API server
        self._logger.info("Stop API server")
        self._api_server.should_exit = True
        self._api_server.force_exit = True
        self._logger.info("API server stopped")

        # Stop all tasks
        for task in self._tasks:
            task.cancel()
        self._logger.info("Tasks cancelled")

        # Stop the event loop
        loop = asyncio.get_event_loop()
        asyncio.tasks.all_tasks(loop).clear()
        self._logger.info("Tasks cleared")
        loop.stop()
        self._logger.info("Event loop stopped")

        # Stop threads
        if api_app.data_update.update_thread is not None:
            api_app.data_update.update_thread.join(timeout=2)
        if api_app.data_update.update_media_thread is not None:
            api_app.data_update.update_media_thread.join(timeout=2)
        self._logger.info("Threads joined")

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

    async def update_data(self) -> None:
        """Update data."""
        self._logger.info("Update data")
        api_app.data_update.request_update_data()
        self._logger.info("Schedule next update in 60 seconds")
        await asyncio.sleep(60)
        self._logger.info("Sleep finished")

    async def update_media_data(self) -> None:
        """Update media data."""
        self._logger.info("Update media data")
        api_app.data_update.request_update_media_data()
        asyncio.get_running_loop().run_forever()
