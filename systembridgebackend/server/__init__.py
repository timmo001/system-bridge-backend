"""System Bridge: Server"""
import asyncio
import sys
from collections.abc import Callable

import uvicorn
from systembridgemodels.action import Action
from systembridgemodels.settings import SettingHotkey
from systembridgeshared.base import Base
from systembridgeshared.settings import Settings

from ..data import DataUpdate
from ..gui import GUI
from ..modules.listeners import Listeners
from ..server.mdns import MDNSAdvertisement
from ..utilities.action import ActionHandler
from ..utilities.keyboard import keyboard_hotkey_register
from .api import app as api_app


class APIServer(uvicorn.Server):
    """Customized uvicorn.Server

    Uvicorn server overrides signals and we need to include
    Tasks to the signals."""

    def __init__(
        self,
        config: uvicorn.Config,
        exit_callback: Callable[[], None],
    ) -> None:
        super().__init__(config)
        self._exit_callback = exit_callback

    def handle_exit(self, sig: int, frame) -> None:
        """Handle exit."""
        self._exit_callback()
        return super().handle_exit(sig, frame)


class Server(Base):
    """Server"""

    def __init__(
        self,
        settings: Settings,
        listeners: Listeners,
        no_frontend: bool = False,
        no_gui: bool = False,
    ) -> None:
        """Initialise"""
        super().__init__()
        self.no_frontend = no_frontend
        self.no_gui = no_gui

        self._gui_notification: GUI | None = None
        self._gui_player: GUI | None = None
        self._gui: GUI | None = None
        self._listeners = listeners
        self._settings = settings
        self._tasks: list[asyncio.Task] = []

        self._mdns_advertisement = MDNSAdvertisement(settings)
        self._mdns_advertisement.advertise_server()

        self._logger.info("Setup API app")
        api_app.callback_exit = self.exit_application
        api_app.callback_open_gui = self.callback_open_gui
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
        self._data_update = DataUpdate(self.data_updated_callback)
        self._logger.info("Server Initialised")

    async def start(self) -> None:
        """Start the server"""
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
                # api_app.loop.create_task(
                #     self.indefinite_func_wrapper(self.update_frequent_data),
                #     name="Update frequent data",
                # ),
                # api_app.loop.create_task(
                #     self.update_events_data(),
                #     name="Update events data",
                # ),
            ]
        )
        if not self.no_gui:
            self._gui = GUI(self._settings)
            self._tasks.extend(
                [
                    api_app.loop.create_task(
                        self._gui.start(self.exit_application),
                        name="GUI",
                    ),
                    api_app.loop.create_task(
                        self.register_hotkeys(),
                        name="Register hotkeys",
                    ),
                ]
            )

        await asyncio.wait(self._tasks)

    async def data_updated_callback(
        self,
        module: str,
    ) -> None:
        """Data updated"""
        await self._listeners.refresh_data_by_module(
            self._data_update.data,
            module,
        )

    def callback_open_gui(
        self,
        command: str,
        data: str,
    ) -> None:
        """Open GUI"""
        if command == "notification":
            if self._gui_notification:
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

    async def indefinite_func_wrapper(self, func) -> None:
        """Indefinite function wrapper"""
        while True:
            await func()

    def exit_application(self) -> None:
        """Exit application"""
        self._logger.info("Exiting application")
        for task in self._tasks:
            task.cancel()
        self._logger.info("Tasks cancelled")
        if self._gui:
            self._gui.stop()
        if self._gui_notification:
            self._gui_notification.stop()
        if self._gui_player:
            self._gui_player.stop()
        self._logger.info("GUI stopped. Exiting Application")
        sys.exit(0)

    async def register_hotkeys(self) -> None:
        """Register hotkeys"""
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
        """Register hotkey"""
        self._logger.info("Register hotkey: %s", hotkey)

        def hotkey_callback() -> None:
            """Hotkey callback"""
            self._logger.info("Hotkey pressed: %s", hotkey)
            # TODO: Implement action handler
            # action_handler = ActionHandler(self._settings)
            # api_app.loop.create_task(action_handler.handle(Action(hotkey.key))

        keyboard_hotkey_register(
            hotkey.key,
            hotkey_callback,
        )

    async def update_data(self) -> None:
        """Update data"""
        self._logger.info("Update data")
        self._data_update.request_update_data()
        self._logger.info("Schedule next update in 2 minutes")
        await asyncio.sleep(120)

    # async def update_events_data(self) -> None:
    #     """Update events data"""
    #     self._logger.info("Update events data")
    #     self._data.request_update_events_data()
    #     asyncio.get_running_loop().run_forever()

    # async def update_frequent_data(self) -> None:
    #     """Update frequent data"""
    #     self._logger.info("Update frequent data")
    #     self._data.request_update_frequent_data()
    #     self._logger.info("Schedule next frequent update in 30 seconds")
    #     await asyncio.sleep(30)
