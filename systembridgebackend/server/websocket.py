"""WebSocket Handler."""

from collections.abc import Callable
from dataclasses import asdict, is_dataclass
from json import JSONDecodeError
import os
from uuid import uuid4

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from systembridgemodels.keyboard_key import KeyboardKey
from systembridgemodels.keyboard_text import KeyboardText
from systembridgemodels.media_control import MediaAction, MediaControl
from systembridgemodels.media_get_file import MediaGetFile
from systembridgemodels.media_get_files import MediaGetFiles
from systembridgemodels.modules import GetData, ModulesData, RegisterDataListener
from systembridgemodels.notification import Notification
from systembridgemodels.open_path import OpenPath
from systembridgemodels.open_url import OpenUrl
from systembridgemodels.request import Request
from systembridgemodels.response import Response
from systembridgemodels.update import Update as UpdateModel
from systembridgeshared.base import Base
from systembridgeshared.const import (
    EVENT_BASE,
    EVENT_DATA,
    EVENT_EVENT,
    EVENT_MESSAGE,
    EVENT_MODULES,
    EVENT_PATH,
    EVENT_URL,
    SUBTYPE_BAD_DIRECTORY,
    SUBTYPE_BAD_FILE,
    SUBTYPE_BAD_JSON,
    SUBTYPE_BAD_PATH,
    SUBTYPE_BAD_REQUEST,
    SUBTYPE_BAD_TOKEN,
    SUBTYPE_INVALID_ACTION,
    SUBTYPE_LISTENER_ALREADY_REGISTERED,
    SUBTYPE_LISTENER_NOT_REGISTERED,
    SUBTYPE_MISSING_ACTION,
    SUBTYPE_MISSING_KEY,
    SUBTYPE_MISSING_MODULES,
    SUBTYPE_MISSING_PATH_URL,
    SUBTYPE_MISSING_TEXT,
    SUBTYPE_MISSING_TITLE,
    SUBTYPE_MISSING_VALUE,
    SUBTYPE_UNKNOWN_EVENT,
    TYPE_APPLICATION_UPDATE,
    TYPE_APPLICATION_UPDATING,
    TYPE_DATA_GET,
    TYPE_DATA_LISTENER_REGISTERED,
    TYPE_DATA_LISTENER_UNREGISTERED,
    TYPE_DATA_UPDATE,
    TYPE_DIRECTORIES,
    TYPE_ERROR,
    TYPE_EXIT_APPLICATION,
    TYPE_FILE,
    TYPE_FILES,
    TYPE_GET_DATA,
    TYPE_GET_DIRECTORIES,
    TYPE_GET_FILE,
    TYPE_GET_FILES,
    TYPE_GET_SETTINGS,
    TYPE_KEYBOARD_KEY_PRESSED,
    TYPE_KEYBOARD_KEYPRESS,
    TYPE_KEYBOARD_TEXT,
    TYPE_KEYBOARD_TEXT_SENT,
    TYPE_MEDIA_CONTROL,
    TYPE_NOTIFICATION,
    TYPE_NOTIFICATION_SENT,
    TYPE_OPEN,
    TYPE_OPENED,
    TYPE_POWER_HIBERNATE,
    TYPE_POWER_HIBERNATING,
    TYPE_POWER_LOCK,
    TYPE_POWER_LOCKING,
    TYPE_POWER_LOGGINGOUT,
    TYPE_POWER_LOGOUT,
    TYPE_POWER_RESTART,
    TYPE_POWER_RESTARTING,
    TYPE_POWER_SHUTDOWN,
    TYPE_POWER_SHUTTINGDOWN,
    TYPE_POWER_SLEEP,
    TYPE_POWER_SLEEPING,
    TYPE_REGISTER_DATA_LISTENER,
    TYPE_SETTINGS_RESULT,
    TYPE_UNREGISTER_DATA_LISTENER,
    TYPE_UPDATE_SETTINGS,
)
from systembridgeshared.settings import Settings
from systembridgeshared.update import Update

from ..handlers.data import DataUpdate
from ..handlers.keyboard import keyboard_keypress, keyboard_text
from ..handlers.media import (
    control_fastforward,
    control_mute,
    control_next,
    control_pause,
    control_play,
    control_previous,
    control_repeat,
    control_rewind,
    control_seek,
    control_shuffle,
    control_stop,
    control_volume_down,
    control_volume_up,
    get_directories,
    get_file,
    get_files,
)
from ..handlers.open import open_path, open_url
from ..handlers.power import hibernate, lock, logout, restart, shutdown, sleep
from ..modules import MODULES
from ..modules.listeners import Listeners


class WebSocketHandler(Base):
    """WebSocket handler."""

    def __init__(
        self,
        settings: Settings,
        data_update: DataUpdate,
        listeners: Listeners,
        websocket: WebSocket,
        callback_exit_application: Callable[[], None],
    ) -> None:
        """Initialise."""
        super().__init__()
        self._settings = settings
        self._data_update = data_update
        self._listeners = listeners
        self._websocket = websocket
        self._callback_exit_application = callback_exit_application
        self._active = True

    async def _send_response(
        self,
        response: Response,
    ) -> None:
        """Send response."""
        if not self._active:
            return
        message = asdict(response)
        self._logger.debug("Sending message: %s", message)
        if self._websocket is None:
            self._logger.error("Websocket is None")
            return
        await self._websocket.send_json(message)

    async def _data_changed(
        self,
        module: str,
        data: ModulesData,
    ) -> None:
        """Change data."""
        if module not in MODULES:
            self._logger.info("Data module %s not in registered modules", module)
            return
        data_module = getattr(data, module)

        await self._send_response(
            Response(
                id=str(uuid4()),
                type=TYPE_DATA_UPDATE,
                message="Data changed",
                module=module,
                data=asdict(data_module) if is_dataclass(data_module) else data_module,
            )
        )

    async def _handle_event(  # noqa: C901
        self,
        listener_id: str,
        response_data: dict,
        request: Request,
    ) -> None:
        """Handle event."""
        if request.event == TYPE_APPLICATION_UPDATE:
            try:
                model = UpdateModel(**response_data[EVENT_DATA])
            except ValueError as error:
                message = f"Invalid request: {error}"
                self._logger.warning(message, exc_info=error)
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_REQUEST,
                        message=message,
                        data={},
                    )
                )
                return
            versions = Update().update(
                model.version,
                wait=False,
            )
            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_APPLICATION_UPDATING,
                    message="Updating application",
                    data=versions,
                )
            )
        elif request.event == TYPE_EXIT_APPLICATION:
            self._callback_exit_application()
            self._logger.info("Exit application called")
        elif request.event == TYPE_KEYBOARD_KEYPRESS:
            try:
                model = KeyboardKey(**response_data[EVENT_DATA])
            except ValueError as error:
                message = f"Invalid request: {error}"
                self._logger.warning(message, exc_info=error)
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_REQUEST,
                        data={EVENT_MESSAGE: message},
                    )
                )
                return
            if model.key is None:
                self._logger.warning("No key provided")
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_MISSING_KEY,
                        data={EVENT_MESSAGE: "No key provided"},
                    )
                )
                return

            try:
                keyboard_keypress(model.key)
            except ValueError as err:
                self._logger.warning("ValueError", exc_info=err)
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_MISSING_KEY,
                        data={EVENT_MESSAGE: "Invalid key"},
                    )
                )
                return

            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_KEYBOARD_KEY_PRESSED,
                    data={
                        EVENT_MESSAGE: "Key pressed",
                        "key": model.key,
                    },
                )
            )
        elif request.event == TYPE_KEYBOARD_TEXT:
            try:
                model = KeyboardText(**response_data[EVENT_DATA])
            except ValueError as error:
                message = f"Invalid request: {error}"
                self._logger.warning(message, exc_info=error)
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_REQUEST,
                        data={EVENT_MESSAGE: message},
                    )
                )
                return
            if model.text is None:
                self._logger.warning("No text provided")
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_MISSING_TEXT,
                        data={EVENT_MESSAGE: "No text provided"},
                    )
                )
                return

            keyboard_text(model.text)

            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_KEYBOARD_TEXT_SENT,
                    message="Key pressed",
                    data={"text": model.text},
                )
            )
        elif request.event == TYPE_MEDIA_CONTROL:
            try:
                model = MediaControl(**response_data[EVENT_DATA])
            except ValueError as error:
                message = f"Invalid request: {error}"
                self._logger.warning(message, exc_info=error)
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_REQUEST,
                        message=message,
                        data={},
                    )
                )
                return
            if model.action is None:
                self._logger.warning("No action provided")
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_MISSING_ACTION,
                        message="No action provided",
                        data={},
                    )
                )
                return
            if model.action not in MediaAction:
                self._logger.warning("Invalid action provided")
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_INVALID_ACTION,
                        message="Invalid action provided",
                        data={},
                    )
                )
                return
            if model.action == MediaAction.PLAY:
                await control_play()
            elif model.action == MediaAction.PAUSE:
                await control_pause()
            elif model.action == MediaAction.STOP:
                await control_stop()
            elif model.action == MediaAction.PREVIOUS:
                await control_previous()
            elif model.action == MediaAction.NEXT:
                await control_next()
            elif model.action == MediaAction.SEEK:
                if model.value is None:
                    self._logger.warning("No position value provided")
                    await self._send_response(
                        Response(
                            id=request.id,
                            type=TYPE_ERROR,
                            subtype=SUBTYPE_MISSING_VALUE,
                            message="No value provided",
                            data={},
                        )
                    )
                    return
                await control_seek(int(model.value))
            elif model.action == MediaAction.REWIND:
                await control_rewind()
            elif model.action == MediaAction.FASTFORWARD:
                await control_fastforward()
            elif model.action == MediaAction.SHUFFLE:
                if model.value is None:
                    self._logger.warning("No shuffle value provided")
                    await self._send_response(
                        Response(
                            id=request.id,
                            type=TYPE_ERROR,
                            subtype=SUBTYPE_MISSING_VALUE,
                            message="No value provided",
                            data={},
                        )
                    )
                    return
                await control_shuffle(bool(model.value))
            elif model.action == MediaAction.REPEAT:
                if model.value is None:
                    self._logger.warning("No repeat value provided")
                    await self._send_response(
                        Response(
                            id=request.id,
                            type=TYPE_ERROR,
                            subtype=SUBTYPE_MISSING_VALUE,
                            message="No value provided",
                            data={},
                        )
                    )
                    return
                await control_repeat(int(model.value))
            elif model.action == MediaAction.MUTE:
                await control_mute()
            elif model.action == MediaAction.VOLUMEDOWN:
                await control_volume_down()
            elif model.action == MediaAction.VOLUMEUP:
                await control_volume_up()

        elif request.event == TYPE_NOTIFICATION:
            try:
                model = Notification(**response_data[EVENT_DATA])
            except ValueError as error:
                message = f"Invalid request: {error}"
                self._logger.warning(message, exc_info=error)
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_REQUEST,
                        message=message,
                        data={},
                    )
                )
                return
            if model.title is None:
                self._logger.warning("No title provided")
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_MISSING_TITLE,
                        message="No title provided",
                        data={},
                    )
                )
                return

            self._logger.warning("Sending notification: %s", model.title)
            for listener in self._listeners.registered_listeners:
                self._logger.warning(
                    "Sending notification to listener: %s", listener.id
                )
                await listener.send_response(
                    Response(
                        id=request.id,
                        type=TYPE_NOTIFICATION,
                        data=asdict(model),
                    )
                )

            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_NOTIFICATION_SENT,
                    message="Notification sent",
                    data=asdict(model),
                )
            )
        elif request.event == TYPE_OPEN:
            if "path" in response_data[EVENT_DATA]:
                try:
                    model = OpenPath(**response_data[EVENT_DATA])
                except ValueError as error:
                    message = f"Invalid request: {error}"
                    self._logger.warning(message, exc_info=error)
                    await self._send_response(
                        Response(
                            id=request.id,
                            type=TYPE_ERROR,
                            subtype=SUBTYPE_BAD_REQUEST,
                            message=message,
                            data={},
                        )
                    )
                    return
                open_path(model.path)  # pylint: disable=no-member
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_OPENED,
                        subtype=SUBTYPE_MISSING_PATH_URL,
                        message="Path opened",
                        data={EVENT_PATH: model.path},
                    )
                )
                return
            if "url" in response_data[EVENT_DATA]:
                try:
                    model = OpenUrl(**response_data[EVENT_DATA])
                except ValueError as error:
                    message = f"Invalid request: {error}"
                    self._logger.warning(message, exc_info=error)
                    await self._send_response(
                        Response(
                            id=request.id,
                            type=TYPE_ERROR,
                            subtype=SUBTYPE_BAD_REQUEST,
                            message=message,
                            data={},
                        )
                    )
                    return
                open_url(model.url)  # pylint: disable=no-member
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_OPENED,
                        subtype=SUBTYPE_MISSING_PATH_URL,
                        message="URL opened",
                        data={EVENT_URL: model.url},
                    )
                )
                return

            self._logger.warning("No path or url provided")
            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_ERROR,
                    subtype=SUBTYPE_MISSING_PATH_URL,
                    message="No path or url provided",
                    data={},
                )
            )
        elif request.event == TYPE_REGISTER_DATA_LISTENER:
            try:
                model = RegisterDataListener(
                    modules=response_data[EVENT_DATA][EVENT_MODULES]
                )
            except ValueError as error:
                message = f"Invalid request: {error}"
                self._logger.warning(message, exc_info=error)
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_REQUEST,
                        data={EVENT_MESSAGE: message},
                    )
                )
                return
            if model.modules is None or len(model.modules) == 0:
                self._logger.warning("No modules provided")
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_MISSING_MODULES,
                        data={EVENT_MESSAGE: "No modules provided"},
                    )
                )
                return

            self._logger.info(
                "Registering data listener: %s - %s",
                listener_id,
                model.modules,
            )

            if await self._listeners.add_listener(
                listener_id,
                self._send_response,
                self._data_changed,
                model.modules,
            ):
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_LISTENER_ALREADY_REGISTERED,
                        data={
                            EVENT_MESSAGE: "Listener already registered with this connection",
                            EVENT_MODULES: model.modules,
                        },
                    )
                )
                return

            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_DATA_LISTENER_REGISTERED,
                    message="Data listener registered",
                    data={EVENT_MODULES: model.modules},
                )
            )
        elif request.event == TYPE_UNREGISTER_DATA_LISTENER:
            self._logger.info("Unregistering data listener %s", listener_id)

            if not self._listeners.remove_listener(listener_id):
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_LISTENER_NOT_REGISTERED,
                        data={
                            EVENT_MESSAGE: "Listener not registered with this connection",
                        },
                    )
                )
                return

            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_DATA_LISTENER_UNREGISTERED,
                    data={
                        EVENT_MESSAGE: "Data listener unregistered",
                    },
                )
            )
        elif request.event == TYPE_GET_DATA:
            try:
                model = GetData(modules=response_data[EVENT_DATA][EVENT_MODULES])
            except ValueError as error:
                message = f"Invalid request: {error}"
                self._logger.warning(message, exc_info=error)
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_REQUEST,
                        data={EVENT_MESSAGE: message},
                    )
                )
                return
            if model.modules is None or len(model.modules) == 0:
                self._logger.warning("No modules provided")
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_MISSING_MODULES,
                        data={EVENT_MESSAGE: "No modules provided"},
                    )
                )
                return
            self._logger.info("Getting data: %s", model.modules)

            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_DATA_GET,
                    message="Getting data",
                    data={EVENT_MODULES: model.modules},
                )
            )

            for module in model.modules:
                if (
                    response_data := getattr(self._data_update.data, str(module))
                ) is None:
                    await self._send_response(
                        Response(
                            id=request.id,
                            type=TYPE_ERROR,
                            message="Cannot find data for module",
                            module=str(module),
                            data={},
                        )
                    )
                else:
                    await self._send_response(
                        Response(
                            id=request.id,
                            type=TYPE_DATA_UPDATE,
                            message="Data received",
                            module=str(module),
                            data=response_data,
                        )
                    )

        elif request.event == TYPE_GET_DIRECTORIES:
            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_DIRECTORIES,
                    message="Got directories",
                    data=get_directories(self._settings),
                )
            )
        elif request.event == TYPE_GET_FILES:
            try:
                model = MediaGetFiles(**response_data[EVENT_DATA])
            except ValueError as error:
                message = f"Invalid request: {error}"
                self._logger.warning(message, exc_info=error)
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_REQUEST,
                        message=message,
                        data={},
                    )
                )
                return

            root_path = None
            for item in get_directories(self._settings):
                if item["key"] == model.base:
                    root_path = item["path"]
                    break

            if root_path is None or not os.path.exists(root_path):
                self._logger.warning("Cannot find base path")
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_PATH,
                        message="Cannot find base path",
                        data={EVENT_BASE: model.base},
                    )
                )
                return

            path = (
                os.path.join(root_path, model.path)
                if model.path is not None
                else root_path
            )

            self._logger.info(
                "Getting files: %s - %s - %s",
                model.base,
                model.path,
                path,
            )

            if not os.path.exists(path):
                self._logger.warning("Cannot find path")
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_PATH,
                        message="Cannot find path",
                        data={EVENT_PATH: path},
                    )
                )
                return
            if not os.path.isdir(path):
                self._logger.warning("Path is not a directory")
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_DIRECTORY,
                        message="Path is not a directory",
                        data={EVENT_PATH: path},
                    )
                )
                return

            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_FILES,
                    message="Got files",
                    data=get_files(self._settings, model.base, path),
                )
            )
        elif request.event == TYPE_GET_FILE:
            try:
                model = MediaGetFile(**response_data[EVENT_DATA])
            except ValueError as error:
                message = f"Invalid request: {error}"
                self._logger.warning(message, exc_info=error)
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_REQUEST,
                        message=message,
                        data={},
                    )
                )
                return

            root_path = None
            for item in get_directories(self._settings):
                if item["key"] == model.base:
                    root_path = item["path"]
                    break

            if root_path is None or not os.path.exists(root_path):
                self._logger.warning("Cannot find base path")
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_PATH,
                        message="Cannot find base path",
                        data={EVENT_BASE: model.base},
                    )
                )
                return

            path = os.path.join(root_path, model.path)

            self._logger.info(
                "Getting file: %s - %s - %s",
                model.base,
                model.path,
                path,
            )

            if not os.path.exists(path):
                self._logger.warning("Cannot find path")
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_PATH,
                        message="Cannot find path",
                        data={EVENT_PATH: path},
                    )
                )
                return
            if not os.path.isfile(path):
                self._logger.warning("Path is not a file")
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_FILE,
                        message="Path is not a file",
                        data={EVENT_PATH: path},
                    )
                )
                return

            if (file := get_file(root_path, path)) is not None:
                response_data = asdict(file)
            else:
                response_data = {}

            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_FILE,
                    message="Got file",
                    data=response_data[EVENT_DATA],
                )
            )
        elif request.event == TYPE_GET_SETTINGS:
            self._logger.info("Getting settings")
            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_SETTINGS_RESULT,
                    message="Got settings",
                    data=asdict(self._settings.data),
                )
            )
        elif request.event == TYPE_UPDATE_SETTINGS:
            self._logger.info("Updating settings")
            self._settings.update(response_data[EVENT_DATA])
            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_SETTINGS_RESULT,
                    message="Updated settings",
                    data=asdict(self._settings.data),
                )
            )
        elif request.event == TYPE_POWER_SLEEP:
            self._logger.info("Sleeping")
            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_POWER_SLEEPING,
                    message="Sleeping",
                    data={},
                )
            )
            sleep()
        elif request.event == TYPE_POWER_HIBERNATE:
            self._logger.info("Sleeping")
            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_POWER_HIBERNATING,
                    message="Hibernating",
                    data={},
                )
            )
            hibernate()
        elif request.event == TYPE_POWER_RESTART:
            self._logger.info("Sleeping")
            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_POWER_RESTARTING,
                    message="Restarting",
                    data={},
                )
            )
            restart()
        elif request.event == TYPE_POWER_SHUTDOWN:
            self._logger.info("Sleeping")
            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_POWER_SHUTTINGDOWN,
                    message="Shutting down",
                    data={},
                )
            )
            shutdown()
        elif request.event == TYPE_POWER_LOCK:
            self._logger.info("Locking")
            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_POWER_LOCKING,
                    message="Locking",
                    data={},
                )
            )
            lock()
        elif request.event == TYPE_POWER_LOGOUT:
            self._logger.info("Logging out")
            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_POWER_LOGGINGOUT,
                    message="Logging out",
                    data={},
                )
            )
            logout()
        else:
            self._logger.warning("Unknown event: %s", request.event)
            await self._send_response(
                Response(
                    id=request.id,
                    type=TYPE_ERROR,
                    subtype=SUBTYPE_UNKNOWN_EVENT,
                    data={
                        EVENT_MESSAGE: "Unknown event",
                        EVENT_EVENT: request.event,
                    },
                )
            )

    async def _handler(
        self,
        listener_id: str,
    ) -> None:
        """Handle the websocket connection."""
        # Loop until the connection is closed
        while self._active:
            try:
                if self._websocket is None:
                    self._logger.error("Websocket is None")
                    continue
                data = await self._websocket.receive_json()
                request = Request(**data)
            except JSONDecodeError as error:
                message = f"Invalid JSON: {error}"
                self._logger.error(message, exc_info=error)
                await self._send_response(
                    Response(
                        id="UNKNOWN",
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_JSON,
                        data={EVENT_MESSAGE: message},
                    )
                )
                return
            except ValueError as error:
                message = f"Invalid request: {error}"
                self._logger.error(message, exc_info=error)
                await self._send_response(
                    Response(
                        id="UNKNOWN",
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_REQUEST,
                        data={EVENT_MESSAGE: message},
                    )
                )
                return

            self._logger.info("Received: %s", request.event)

            if request.token != self._settings.data.api.token:
                self._logger.warning(
                    "Invalid token: %s != %s",
                    request.token,
                    self._settings.data.api.token,
                )
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_BAD_TOKEN,
                        data={EVENT_MESSAGE: "Invalid token"},
                    )
                )
                return

            try:
                await self._handle_event(
                    listener_id,
                    data,
                    request,
                )
            except Exception as error:  # pylint: disable=broad-except
                self._logger.error(error, exc_info=error)
                await self._send_response(
                    Response(
                        id=request.id,
                        type=TYPE_ERROR,
                        subtype=SUBTYPE_UNKNOWN_EVENT,
                        data={EVENT_MESSAGE: str(error)},
                    )
                )

    async def handler(self) -> None:
        """Handle the websocket connection."""
        listener_id = str(uuid4())
        try:
            await self._handler(listener_id)
        except (ConnectionError, WebSocketDisconnect) as error:
            self._logger.info("Connection closed: %s", error)
        finally:
            self._logger.info("Unregistering data listener %s", listener_id)
            self._listeners.remove_listener(listener_id)

    def set_active(
        self,
        active: bool,
    ) -> None:
        """Set active."""
        self._active = active
