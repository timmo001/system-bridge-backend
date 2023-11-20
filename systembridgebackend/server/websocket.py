"""WebSocket Handler"""
import os
from collections.abc import Callable
from dataclasses import asdict
from json import JSONDecodeError
from uuid import uuid4

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect
from systembridgemodels.data import Data
from systembridgemodels.get_data import GetData
from systembridgemodels.get_setting import GetSetting
from systembridgemodels.keyboard_key import KeyboardKey
from systembridgemodels.keyboard_text import KeyboardText
from systembridgemodels.media_control import Action as MediaAction
from systembridgemodels.media_control import MediaControl
from systembridgemodels.media_get_file import MediaGetFile
from systembridgemodels.media_get_files import MediaGetFiles
from systembridgemodels.notification import Notification
from systembridgemodels.open_path import OpenPath
from systembridgemodels.open_url import OpenUrl
from systembridgemodels.register_data_listener import RegisterDataListener
from systembridgemodels.request import Request
from systembridgemodels.response import Response
from systembridgemodels.update import Update as UpdateModel
from systembridgemodels.update_setting import UpdateSetting
from systembridgeshared.base import Base
from systembridgeshared.const import (
    EVENT_DATA,
    EVENT_EVENT,
    EVENT_MESSAGE,
    EVENT_MODULES,
    SUBTYPE_BAD_JSON,
    SUBTYPE_BAD_REQUEST,
    SUBTYPE_BAD_TOKEN,
    SUBTYPE_LISTENER_ALREADY_REGISTERED,
    SUBTYPE_LISTENER_NOT_REGISTERED,
    SUBTYPE_MISSING_KEY,
    SUBTYPE_MISSING_MODULES,
    SUBTYPE_MISSING_TEXT,
    SUBTYPE_UNKNOWN_EVENT,
    TYPE_APPLICATION_UPDATE,
    TYPE_APPLICATION_UPDATING,
    TYPE_DATA_GET,
    TYPE_DATA_LISTENER_REGISTERED,
    TYPE_DATA_LISTENER_UNREGISTERED,
    TYPE_DATA_UPDATE,
    TYPE_ERROR,
    TYPE_EXIT_APPLICATION,
    TYPE_GET_DATA,
    TYPE_KEYBOARD_KEY_PRESSED,
    TYPE_KEYBOARD_KEYPRESS,
    TYPE_KEYBOARD_TEXT,
    TYPE_KEYBOARD_TEXT_SENT,
    TYPE_REGISTER_DATA_LISTENER,
    TYPE_UNREGISTER_DATA_LISTENER,
)
from systembridgeshared.settings import Settings
from systembridgeshared.update import Update

from ..data import DataUpdate
from ..modules import MODULES
from ..modules.listeners import Listeners
from ..utilities.autostart import autostart_disable, autostart_enable
from ..utilities.keyboard import keyboard_keypress, keyboard_text
from ..utilities.media import (
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
from ..utilities.open import open_path, open_url
from ..utilities.power import hibernate, lock, logout, restart, shutdown, sleep


class WebSocketHandler(Base):
    """WebSocket handler"""

    def __init__(
        self,
        settings: Settings,
        data_update: DataUpdate,
        listeners: Listeners,
        websocket: WebSocket,
        callback_exit_application: Callable[[], None],
        callback_open_gui: Callable[[str, str], None],
    ) -> None:
        """Initialise"""
        super().__init__()
        self._settings = settings
        self._data_update = data_update
        self._listeners = listeners
        self._websocket = websocket
        self._callback_exit_application = callback_exit_application
        self._callback_open_gui = callback_open_gui
        self._active = True

    async def _send_response(
        self,
        response: Response,
    ) -> None:
        """Send response"""
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
        data: Data,
    ) -> None:
        """Data changed"""
        if module not in MODULES:
            self._logger.info("Data module %s not in registered modules", module)
            return
        await self._send_response(
            Response(
                id=str(uuid4()),
                type=TYPE_DATA_UPDATE,
                message="Data changed",
                module=module,
                data=asdict(getattr(data, module)),
            )
        )

    async def _handle_event(
        self,
        listener_id: str,
        data: dict,
        request: Request,
    ) -> None:
        """Handle event"""
        if request.event == TYPE_APPLICATION_UPDATE:
            try:
                model = UpdateModel(**data)
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
                model = KeyboardKey(**data)
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
                model = KeyboardText(**data)
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
        # elif request.event == TYPE_MEDIA_CONTROL:
        #     try:
        #         model = MediaControl(**data)
        #     except ValueError as error:
        #         message = f"Invalid request: {error}"
        #         self._logger.warning(message, exc_info=error)
        #         await self._send_response(
        #             Response(
        #                 **{
        #                     EVENT_ID: request.id,
        #                     EVENT_TYPE: TYPE_ERROR,
        #                     EVENT_SUBTYPE: SUBTYPE_BAD_REQUEST,
        #                     EVENT_MESSAGE: message,
        #                 }
        #             )
        #         )
        #         return
        #     if model.action is None:
        #         self._logger.warning("No action provided")
        #         await self._send_response(
        #             Response(
        #                 **{
        #                     EVENT_ID: request.id,
        #                     EVENT_TYPE: TYPE_ERROR,
        #                     EVENT_SUBTYPE: SUBTYPE_MISSING_ACTION,
        #                     EVENT_MESSAGE: "No action provided",
        #                 }
        #             )
        #         )
        #         return
        #     if model.action not in MediaAction:
        #         self._logger.warning("Invalid action provided")
        #         await self._send_response(
        #             Response(
        #                 **{
        #                     EVENT_ID: request.id,
        #                     EVENT_TYPE: TYPE_ERROR,
        #                     EVENT_SUBTYPE: SUBTYPE_INVALID_ACTION,
        #                     EVENT_MESSAGE: "Invalid action provided",
        #                 }
        #             )
        #         )
        #         return
        #     if model.action == MediaAction.play:
        #         await control_play()
        #     elif model.action == MediaAction.pause:
        #         await control_pause()
        #     elif model.action == MediaAction.stop:
        #         await control_stop()
        #     elif model.action == MediaAction.previous:
        #         await control_previous()
        #     elif model.action == MediaAction.next:
        #         await control_next()
        #     elif model.action == MediaAction.seek:
        #         if model.value is None:
        #             self._logger.warning("No position value provided")
        #             await self._send_response(
        #                 Response(
        #                     **{
        #                         EVENT_ID: request.id,
        #                         EVENT_TYPE: TYPE_ERROR,
        #                         EVENT_SUBTYPE: SUBTYPE_MISSING_VALUE,
        #                         EVENT_MESSAGE: "No value provided",
        #                     }
        #                 )
        #             )
        #             return
        #         await control_seek(int(model.value))
        #     elif model.action == MediaAction.rewind:
        #         await control_rewind()
        #     elif model.action == MediaAction.fastforward:
        #         await control_fastforward()
        #     elif model.action == MediaAction.shuffle:
        #         if model.value is None:
        #             self._logger.warning("No shuffle value provided")
        #             await self._send_response(
        #                 Response(
        #                     **{
        #                         EVENT_ID: request.id,
        #                         EVENT_TYPE: TYPE_ERROR,
        #                         EVENT_SUBTYPE: SUBTYPE_MISSING_VALUE,
        #                         EVENT_MESSAGE: "No value provided",
        #                     }
        #                 )
        #             )
        #             return
        #         await control_shuffle(bool(model.value))
        #     elif model.action == MediaAction.repeat:
        #         if model.value is None:
        #             self._logger.warning("No repeat value provided")
        #             await self._send_response(
        #                 Response(
        #                     **{
        #                         EVENT_ID: request.id,
        #                         EVENT_TYPE: TYPE_ERROR,
        #                         EVENT_SUBTYPE: SUBTYPE_MISSING_VALUE,
        #                         EVENT_MESSAGE: "No value provided",
        #                     }
        #                 )
        #             )
        #             return
        #         await control_repeat(int(model.value))
        #     elif model.action == MediaAction.mute:
        #         await control_mute()
        #     elif model.action == MediaAction.volumedown:
        #         await control_volume_down()
        #     elif model.action == MediaAction.volumeup:
        #         await control_volume_up()

        # elif request.event == TYPE_NOTIFICATION:
        #     try:
        #         model = Notification(**data)
        #     except ValueError as error:
        #         message = f"Invalid request: {error}"
        #         self._logger.warning(message, exc_info=error)
        #         await self._send_response(
        #             Response(
        #                 **{
        #                     EVENT_ID: request.id,
        #                     EVENT_TYPE: TYPE_ERROR,
        #                     EVENT_SUBTYPE: SUBTYPE_BAD_REQUEST,
        #                     EVENT_MESSAGE: message,
        #                 }
        #             )
        #         )
        #         return
        #     if model.title is None:
        #         self._logger.warning("No title provided")
        #         await self._send_response(
        #             Response(
        #                 **{
        #                     EVENT_ID: request.id,
        #                     EVENT_TYPE: TYPE_ERROR,
        #                     EVENT_SUBTYPE: SUBTYPE_MISSING_TITLE,
        #                     EVENT_MESSAGE: "No title provided",
        #                 }
        #             )
        #         )
        #         return

        #     self._callback_open_gui("notification", model.json())

        #     await self._send_response(
        #         Response(
        #             **{
        #                 EVENT_ID: request.id,
        #                 EVENT_TYPE: TYPE_NOTIFICATION_SENT,
        #                 EVENT_MESSAGE: "Notification sent",
        #             }
        #         )
        #     )
        # elif request.event == TYPE_OPEN:
        #     if "path" in data:
        #         try:
        #             model = OpenPath(**data)
        #         except ValueError as error:
        #             message = f"Invalid request: {error}"
        #             self._logger.warning(message, exc_info=error)
        #             await self._send_response(
        #                 Response(
        #                     **{
        #                         EVENT_ID: request.id,
        #                         EVENT_TYPE: TYPE_ERROR,
        #                         EVENT_SUBTYPE: SUBTYPE_BAD_REQUEST,
        #                         EVENT_MESSAGE: message,
        #                     }
        #                 )
        #             )
        #             return
        #         open_path(model.path)  # pylint: disable=no-member
        #         await self._send_response(
        #             Response(
        #                 **{
        #                     EVENT_ID: request.id,
        #                     EVENT_TYPE: TYPE_OPENED,
        #                     EVENT_MESSAGE: "Path opened",
        #                     EVENT_PATH: model.path,
        #                 }
        #             )
        #         )
        #         return
        #     if "url" in data:
        #         try:
        #             model = OpenUrl(**data)
        #         except ValueError as error:
        #             message = f"Invalid request: {error}"
        #             self._logger.warning(message, exc_info=error)
        #             await self._send_response(
        #                 Response(
        #                     **{
        #                         EVENT_ID: request.id,
        #                         EVENT_TYPE: TYPE_ERROR,
        #                         EVENT_SUBTYPE: SUBTYPE_BAD_REQUEST,
        #                         EVENT_MESSAGE: message,
        #                     }
        #                 )
        #             )
        #             return
        #         open_url(model.url)  # pylint: disable=no-member
        #         await self._send_response(
        #             Response(
        #                 **{
        #                     EVENT_ID: request.id,
        #                     EVENT_TYPE: TYPE_OPENED,
        #                     EVENT_MESSAGE: "URL opened",
        #                     EVENT_URL: model.url,  # pylint: disable=no-member
        #                 }
        #             )
        #         )
        #         return

        #     self._logger.warning("No path or url provided")
        #     await self._send_response(
        #         Response(
        #             **{
        #                 EVENT_ID: request.id,
        #                 EVENT_TYPE: TYPE_ERROR,
        #                 EVENT_SUBTYPE: SUBTYPE_MISSING_PATH_URL,
        #                 EVENT_MESSAGE: "No path or url provided",
        #             }
        #         )
        #     )
        elif request.event == TYPE_REGISTER_DATA_LISTENER:
            try:
                model = RegisterDataListener(modules=data[EVENT_DATA][EVENT_MODULES])
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
                    data={
                        EVENT_MESSAGE: "Data listener registered",
                        EVENT_MODULES: model.modules,
                    },
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
                model = GetData(modules=data[EVENT_DATA][EVENT_MODULES])
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
                if (data := getattr(self._data_update.data, module)) is None:
                    await self._send_response(
                        Response(
                            id=request.id,
                            type=TYPE_ERROR,
                            message="Cannot find data for module",
                            module=module,
                            data={},
                        )
                    )
                else:
                    await self._send_response(
                        Response(
                            id=request.id,
                            type=TYPE_DATA_UPDATE,
                            message="Data received",
                            module=module,
                            data=data,
                        )
                    )

        # elif request.event == TYPE_GET_DIRECTORIES:
        #     await self._send_response(
        #         Response(
        #             **{
        #                 EVENT_ID: request.id,
        #                 EVENT_TYPE: TYPE_DIRECTORIES,
        #                 EVENT_DIRECTORIES: get_directories(self._settings),
        #             }
        #         )
        #     )
        # elif request.event == TYPE_GET_FILES:
        #     try:
        #         model = MediaGetFiles(**data)
        #     except ValueError as error:
        #         message = f"Invalid request: {error}"
        #         self._logger.warning(message, exc_info=error)
        #         await self._send_response(
        #             Response(
        #                 **{
        #                     EVENT_ID: request.id,
        #                     EVENT_TYPE: TYPE_ERROR,
        #                     EVENT_SUBTYPE: SUBTYPE_BAD_REQUEST,
        #                     EVENT_MESSAGE: message,
        #                 }
        #             )
        #         )
        #         return

        #     root_path = None
        #     for item in get_directories(self._settings):
        #         if item["key"] == model.base:
        #             root_path = item["path"]
        #             break

        #     if root_path is None or not os.path.exists(root_path):
        #         self._logger.warning("Cannot find base path")
        #         await self._send_response(
        #             Response(
        #                 **{
        #                     EVENT_ID: request.id,
        #                     EVENT_TYPE: TYPE_ERROR,
        #                     EVENT_SUBTYPE: SUBTYPE_BAD_PATH,
        #                     EVENT_MESSAGE: "Cannot find base path",
        #                     EVENT_BASE: model.base,
        #                 }
        #             )
        #         )
        #         return

        #     path = (
        #         os.path.join(root_path, model.path)
        #         if model.path is not None
        #         else root_path
        #     )

        #     self._logger.info(
        #         "Getting files: %s - %s - %s",
        #         model.base,
        #         model.path,
        #         path,
        #     )

        #     if not os.path.exists(path):
        #         self._logger.warning("Cannot find path")
        #         await self._send_response(
        #             Response(
        #                 **{
        #                     EVENT_ID: request.id,
        #                     EVENT_TYPE: TYPE_ERROR,
        #                     EVENT_SUBTYPE: SUBTYPE_BAD_PATH,
        #                     EVENT_MESSAGE: "Cannot find path",
        #                     EVENT_PATH: path,
        #                 }
        #             )
        #         )
        #         return
        #     if not os.path.isdir(path):
        #         self._logger.warning("Path is not a directory")
        #         await self._send_response(
        #             Response(
        #                 **{
        #                     EVENT_ID: request.id,
        #                     EVENT_TYPE: TYPE_ERROR,
        #                     EVENT_SUBTYPE: SUBTYPE_BAD_DIRECTORY,
        #                     EVENT_MESSAGE: "Path is not a directory",
        #                     EVENT_PATH: path,
        #                 }
        #             )
        #         )
        #         return

        #     await self._send_response(
        #         Response(
        #             **{
        #                 EVENT_ID: request.id,
        #                 EVENT_TYPE: TYPE_FILES,
        #                 EVENT_FILES: get_files(self._settings, model.base, path),
        #                 EVENT_PATH: path,
        #             }
        #         )
        #     )
        # elif request.event == TYPE_GET_FILE:
        #     try:
        #         model = MediaGetFile(**data)
        #     except ValueError as error:
        #         message = f"Invalid request: {error}"
        #         self._logger.warning(message, exc_info=error)
        #         await self._send_response(
        #             Response(
        #                 **{
        #                     EVENT_ID: request.id,
        #                     EVENT_TYPE: TYPE_ERROR,
        #                     EVENT_SUBTYPE: SUBTYPE_BAD_REQUEST,
        #                     EVENT_MESSAGE: message,
        #                 }
        #             )
        #         )
        #         return

        #     root_path = None
        #     for item in get_directories(self._settings):
        #         if item["key"] == model.base:
        #             root_path = item["path"]
        #             break

        #     if root_path is None or not os.path.exists(root_path):
        #         self._logger.warning("Cannot find base path")
        #         await self._send_response(
        #             Response(
        #                 **{
        #                     EVENT_ID: request.id,
        #                     EVENT_TYPE: TYPE_ERROR,
        #                     EVENT_SUBTYPE: SUBTYPE_BAD_PATH,
        #                     EVENT_MESSAGE: "Cannot find base path",
        #                     EVENT_BASE: model.base,
        #                 }
        #             )
        #         )
        #         return

        #     path = os.path.join(root_path, model.path)

        #     self._logger.info(
        #         "Getting file: %s - %s - %s",
        #         model.base,
        #         model.path,
        #         path,
        #     )

        #     if not os.path.exists(path):
        #         self._logger.warning("Cannot find path")
        #         await self._send_response(
        #             Response(
        #                 **{
        #                     EVENT_ID: request.id,
        #                     EVENT_TYPE: TYPE_ERROR,
        #                     EVENT_SUBTYPE: SUBTYPE_BAD_PATH,
        #                     EVENT_MESSAGE: "Cannot find path",
        #                     EVENT_PATH: path,
        #                 }
        #             )
        #         )
        #         return
        #     if not os.path.isfile(path):
        #         self._logger.warning("Path is not a file")
        #         await self._send_response(
        #             Response(
        #                 **{
        #                     EVENT_ID: request.id,
        #                     EVENT_TYPE: TYPE_ERROR,
        #                     EVENT_SUBTYPE: SUBTYPE_BAD_FILE,
        #                     EVENT_MESSAGE: "Path is not a file",
        #                     EVENT_PATH: path,
        #                 }
        #             )
        #         )
        #         return

        #     await self._send_response(
        #         Response(
        #             **{
        #                 EVENT_ID: request.id,
        #                 EVENT_TYPE: TYPE_FILE,
        #                 EVENT_FILE: get_file(root_path, path),
        #                 EVENT_PATH: path,
        #             }
        #         )
        #     )
        # elif request.event == TYPE_GET_SETTINGS:
        #     self._logger.info("Getting settings")
        #     await self._send_response(
        #         Response(
        #             **{
        #                 EVENT_ID: request.id,
        #                 EVENT_TYPE: TYPE_SETTINGS_RESULT,
        #                 EVENT_MESSAGE: "Got settings",
        #                 EVENT_DATA: self._settings.get_all(),
        #             }
        #         )
        #     )
        # elif request.event == TYPE_GET_SETTING:
        #     try:
        #         model = GetSetting(**data)
        #     except ValueError as error:
        #         message = f"Invalid request: {error}"
        #         self._logger.warning(message, exc_info=error)
        #         await self._send_response(
        #             Response(
        #                 **{
        #                     EVENT_ID: request.id,
        #                     EVENT_TYPE: TYPE_ERROR,
        #                     EVENT_SUBTYPE: SUBTYPE_BAD_REQUEST,
        #                     EVENT_MESSAGE: message,
        #                 }
        #             )
        #         )
        #         return

        #     self._logger.info("Getting setting: %s", model.setting)

        #     await self._send_response(
        #         Response(
        #             **{
        #                 EVENT_ID: request.id,
        #                 EVENT_TYPE: TYPE_SETTING_RESULT,
        #                 EVENT_MESSAGE: "Got setting",
        #                 EVENT_SETTING: model.setting,
        #                 EVENT_DATA: self._settings.get(model.setting),
        #             }
        #         )
        #     )
        # elif request.event == TYPE_UPDATE_SETTING:
        #     try:
        #         model = UpdateSetting(**data)
        #     except ValueError as error:
        #         message = f"Invalid request: {error}"
        #         self._logger.warning(message, exc_info=error)
        #         await self._send_response(
        #             Response(
        #                 **{
        #                     EVENT_ID: request.id,
        #                     EVENT_TYPE: TYPE_ERROR,
        #                     EVENT_SUBTYPE: SUBTYPE_BAD_REQUEST,
        #                     EVENT_MESSAGE: message,
        #                 }
        #             )
        #         )
        #         return

        #     self._logger.info(
        #         "Setting setting %s to: %s",
        #         model.setting,
        #         model.value,
        #     )

        #     self._settings.set(model.setting, model.value)

        #     await self._send_response(
        #         Response(
        #             **{
        #                 EVENT_ID: request.id,
        #                 EVENT_TYPE: TYPE_SETTING_UPDATED,
        #                 EVENT_MESSAGE: "Setting updated",
        #                 EVENT_SETTING: model.setting,
        #                 EVENT_VALUE: model.value,
        #             }
        #         )
        #     )

        #     if model.setting != SETTING_AUTOSTART:
        #         return
        #     self._logger.info("Setting autostart to %s", model.value)
        #     if model.value is True:
        #         autostart_enable()
        #     else:
        #         autostart_disable()
        # elif request.event == TYPE_POWER_SLEEP:
        #     self._logger.info("Sleeping")
        #     await self._send_response(
        #         Response(
        #             **{
        #                 EVENT_ID: request.id,
        #                 EVENT_TYPE: TYPE_POWER_SLEEPING,
        #                 EVENT_MESSAGE: "Sleeping",
        #             }
        #         )
        #     )
        #     sleep()
        # elif request.event == TYPE_POWER_HIBERNATE:
        #     self._logger.info("Sleeping")
        #     await self._send_response(
        #         Response(
        #             **{
        #                 EVENT_ID: request.id,
        #                 EVENT_TYPE: TYPE_POWER_HIBERNATING,
        #                 EVENT_MESSAGE: "Hiibernating",
        #             }
        #         )
        #     )
        #     hibernate()
        # elif request.event == TYPE_POWER_RESTART:
        #     self._logger.info("Sleeping")
        #     await self._send_response(
        #         Response(
        #             **{
        #                 EVENT_ID: request.id,
        #                 EVENT_TYPE: TYPE_POWER_RESTARTING,
        #                 EVENT_MESSAGE: "Restarting",
        #             }
        #         )
        #     )
        #     restart()
        # elif request.event == TYPE_POWER_SHUTDOWN:
        #     self._logger.info("Sleeping")
        #     await self._send_response(
        #         Response(
        #             **{
        #                 EVENT_ID: request.id,
        #                 EVENT_TYPE: TYPE_POWER_SHUTTINGDOWN,
        #                 EVENT_MESSAGE: "Shutting down",
        #             }
        #         )
        #     )
        #     shutdown()
        # elif request.event == TYPE_POWER_LOCK:
        #     self._logger.info("Locking")
        #     await self._send_response(
        #         Response(
        #             **{
        #                 EVENT_ID: request.id,
        #                 EVENT_TYPE: TYPE_POWER_LOCKING,
        #                 EVENT_MESSAGE: "Locking",
        #             }
        #         )
        #     )
        #     lock()
        # elif request.event == TYPE_POWER_LOGOUT:
        #     self._logger.info("Logging out")
        #     await self._send_response(
        #         Response(
        #             **{
        #                 EVENT_ID: request.id,
        #                 EVENT_TYPE: TYPE_POWER_LOGGINGOUT,
        #                 EVENT_MESSAGE: "Logging out",
        #             }
        #         )
        #     )
        #     logout()
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
        """Handler"""
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
        """Handler"""
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
        """Set active"""
        self._active = active
