"""API."""
import asyncio
from collections.abc import Callable
from dataclasses import asdict, is_dataclass
from json import dumps
import logging
import os
import sys
from typing import Any

from fastapi import Depends, FastAPI, File, Header, Query, WebSocket, status
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from systembridgemodels.keyboard_key import KeyboardKey
from systembridgemodels.keyboard_text import KeyboardText
from systembridgemodels.media_control import MediaAction, MediaControl
from systembridgemodels.media_files import MediaFile, MediaFiles
from systembridgemodels.notification import Notification
from systembridgemodels.open_path import OpenPath
from systembridgemodels.open_url import OpenUrl
from systembridgeshared.common import asyncio_get_loop
from systembridgeshared.const import HEADER_TOKEN, QUERY_TOKEN
from systembridgeshared.settings import Settings

from .._version import __version__
from ..data import DataUpdate
from ..modules import MODULES
from ..modules.listeners import Listeners
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
    get_file_data,
    get_files,
    write_file,
)
from ..utilities.open import open_path, open_url
from ..utilities.power import (
    hibernate,
    lock,
    logout,
    restart,
    schedule_power_event,
    shutdown,
    sleep,
)
from ..utilities.update import version_update
from .websocket import WebSocketHandler

settings = Settings()

logger = logging.getLogger("systembridgebackend.server.api")


def security_token_header(
    token_header: str | None = Header(alias=HEADER_TOKEN, default=None),
):
    """Get Token from request."""
    if token_header is not None and token_header == settings.data.api.token:
        logger.info("Authorized with Token Header")
        return True
    return False


def security_token_query(
    token_query: str | None = Query(alias=QUERY_TOKEN, default=None),
):
    """Get Token from request."""
    if token_query is not None and token_query == settings.data.api.token:
        logger.info("Authorized with Token Query Parameter")
        return True
    return False


def security_token(
    token_header_result: bool = Depends(security_token_header),
    token_query_result: bool = Depends(security_token_query),
):
    """Get Token from request."""
    logger.info("Token Header Result: %s", token_header_result)
    logger.info("Token Query Result: %s", token_query_result)
    if not (token_header_result or token_query_result):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Token",
        )


class API(FastAPI):
    """Extended FastAPI."""

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        """Initialise."""
        super().__init__(**kwargs)
        self.add_middleware(
            CORSMiddleware,
            allow_credentials=True,
            allow_origins="*",
            allow_headers=[
                "accept",
                "token",
                "content-type",
                "origin",
            ],
            allow_methods=[
                "DELETE",
                "GET",
                "OPTIONS",
                "POST",
                "PUT",
            ],
        )
        self.callback_exit: Callable[[], None]
        self.callback_open_gui: Callable[[str, str], None]
        self.data_update: DataUpdate
        self.listeners: Listeners
        self.loop: asyncio.AbstractEventLoop = asyncio_get_loop()


app = API(
    title="System Bridge",
    version=__version__.public(),
)


@app.get("/")
def get_root() -> dict[str, str]:
    """Get root."""
    return {
        "message": "Hello!",
    }


@app.get("/api", dependencies=[Depends(security_token)])
def get_api_root() -> dict[str, str]:
    """Get API root."""
    return {
        "message": "Hello!",
        "version": __version__.public(),
    }


@app.get("/api/data/{module}", dependencies=[Depends(security_token)])
def get_data(module: str) -> Any:
    """Get data from module."""
    if module not in MODULES:
        logger.info("Data module %s not in registered modules", module)
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"message": f"Data module {module} not found"},
        )

    if (data_module := getattr(app.data_update.data, module)) is None:
        logger.info("Data module %s not found", module)
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"message": f"Data module {module} not found"},
        )

    return asdict(data_module) if is_dataclass(data_module) else data_module


@app.get("/api/data/{module}/{key}", dependencies=[Depends(security_token)])
def get_data_by_key(
    module: str,
    key: str,
) -> dict[str, Any]:
    """Get data from module by key."""
    data = get_data(module)

    if key not in data:
        logger.info("Data item %s in module %s not found", key, module)
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"message": f"Data item {key} in module {module} not found"},
        )

    return {
        key: data[key],
    }


@app.post("/api/keyboard", dependencies=[Depends(security_token)])
def send_keyboard_event(keyboard_event: KeyboardKey | KeyboardText) -> dict[str, str]:
    """Send keyboard event."""
    if isinstance(keyboard_event, KeyboardKey):
        try:
            keyboard_keypress(keyboard_event.key)
        except ValueError as value_error:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail={"error": str(value_error)},
            ) from value_error
        return {
            "message": "Keypress sent",
            **asdict(keyboard_event),
        }
    if isinstance(keyboard_event, KeyboardText):
        keyboard_text(keyboard_event.text)
        return {
            "message": "Text sent",
            **asdict(keyboard_event),
        }
    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid keyboard event")


@app.post("/api/media/control", dependencies=[Depends(security_token)])
async def send_media_control(
    data: MediaControl,
) -> dict[str, str]:
    """Send media control."""
    if data.action not in MediaAction:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Invalid media action",
        )
    if data.action == MediaAction.play:
        await control_play()
    elif data.action == MediaAction.pause:
        await control_pause()
    elif data.action == MediaAction.stop:
        await control_stop()
    elif data.action == MediaAction.previous:
        await control_previous()
    elif data.action == MediaAction.next:
        await control_next()
    elif data.action == MediaAction.seek:
        if data.value is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Invalid seek value",
            )
        await control_seek(int(data.value))
    elif data.action == MediaAction.rewind:
        await control_rewind()
    elif data.action == MediaAction.fastforward:
        await control_fastforward()
    elif data.action == MediaAction.shuffle:
        if data.value is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Invalid shuffle value",
            )
        await control_shuffle(bool(data.value))
    elif data.action == MediaAction.repeat:
        if data.value is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Invalid repeat value",
            )
        await control_repeat(int(data.value))
    elif data.action == MediaAction.mute:
        await control_mute()
    elif data.action == MediaAction.volumedown:
        await control_volume_down()
    elif data.action == MediaAction.volumeup:
        await control_volume_up()
    else:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Invalid media action",
        )

    return {
        "message": "Media control sent",
        **asdict(data),
    }


@app.get("/api/media", dependencies=[Depends(security_token)])
def get_media_directories() -> dict[str, list[dict[str, str]]]:
    """Get media directories."""
    return {
        "directories": get_directories(settings),
    }


@app.get("/api/media/files", dependencies=[Depends(security_token)])
def get_media_files(
    query_base: str = Query(..., alias="base"),
    query_path: str | None = Query(None, alias="path"),
) -> MediaFiles:
    """Get media files."""
    root_path = None
    for item in get_directories(settings):
        if item["key"] == query_base:
            root_path = item["path"]
            break

    if root_path is None or not os.path.exists(root_path):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"message": "Cannot find base", "base": query_base},
        )

    path = os.path.join(root_path, query_path) if query_path else root_path
    if not os.path.exists(path):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            {"message": "Cannot find path", "path": path},
        )
    if not os.path.abspath(path).startswith(os.path.abspath(root_path)):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            {
                "message": "Path is not underneath base path",
                "base": root_path,
                "path": path,
            },
        )
    if not os.path.isdir(path):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            {"message": "Path is not a directory", "path": path},
        )

    return MediaFiles(
        files=get_files(settings, query_base, path),
        path=path,
    )


@app.get("/api/media/file", dependencies=[Depends(security_token)])
def get_media_file(
    query_base: str = Query(..., alias="base"),
    query_path: str = Query(..., alias="path"),
) -> MediaFile:
    """Get media file info."""
    root_path = None
    for item in get_directories(settings):
        if item["key"] == query_base:
            root_path = item["path"]
            break

    if root_path is None or not os.path.exists(root_path):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"message": "Cannot find base", "base": query_base},
        )

    path = os.path.join(root_path, query_path) if query_path else root_path
    if not os.path.exists(path):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            {"message": "Cannot find path", "path": path},
        )
    if not os.path.abspath(path).startswith(os.path.abspath(root_path)):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            {
                "message": "Path is not underneath base path",
                "base": root_path,
                "path": path,
            },
        )
    if not os.path.isfile(path):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            {"message": "Path is not a file", "path": path},
        )

    if (file := get_file(query_base, path)) is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            {"message": "Cannot get file", "path": path},
        )
    return file


@app.get("/api/media/file/data", dependencies=[Depends(security_token)])
def get_media_file_data(
    query_base: str = Query(..., alias="base"),
    query_path: str = Query(..., alias="path"),
) -> FileResponse:
    """Get media file data."""
    root_path = None
    for item in get_directories(settings):
        if item["key"] == query_base:
            root_path = item["path"]
            break

    if root_path is None or not os.path.exists(root_path):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"message": "Cannot find base", "base": query_base},
        )

    path = os.path.join(root_path, query_path) if query_path else root_path
    if not os.path.exists(path):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            {"message": "Cannot find path", "path": path},
        )
    if not os.path.abspath(path).startswith(os.path.abspath(root_path)):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            {
                "message": "Path is not underneath base path",
                "base": root_path,
                "path": path,
            },
        )
    if not os.path.isfile(path):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            {"message": "Path is not a file", "path": path},
        )

    return get_file_data(path)


@app.post("/api/media/file/write", dependencies=[Depends(security_token)])
async def send_media_file(
    query_base: str = Query(..., alias="base"),
    query_path: str = Query(..., alias="path"),
    query_filename: str = Query(..., alias="filename"),
    file: bytes = File(...),
) -> dict[str, str]:
    """Send media file."""
    root_path = None
    for item in get_directories(settings):
        if item["key"] == query_base:
            root_path = item["path"]
            break

    if root_path is None or not os.path.exists(root_path):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={"message": "Cannot find base", "base": query_base},
        )

    path = os.path.join(root_path, query_path) if query_path else root_path
    if not os.path.exists(path):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            {"message": "Cannot find path", "path": path},
        )
    if not os.path.abspath(path).startswith(os.path.abspath(root_path)):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            {
                "message": "Path is not underneath base path",
                "base": root_path,
                "path": path,
            },
        )

    await write_file(os.path.join(path, query_filename), file)

    return {
        "message": "File uploaded",
        "path": path,
        "filename": query_filename,
    }


@app.post("/api/notification", dependencies=[Depends(security_token)])
def send_notification(notification: Notification) -> dict[str, str]:
    """Send notification."""
    app.callback_open_gui(
        "notification",
        dumps(asdict(notification)),
    )
    return {"message": "Notification sent"}


@app.post("/api/open", dependencies=[Depends(security_token)])
def send_open(open_model: OpenPath | OpenUrl) -> dict[str, str]:
    """Send notification."""
    if isinstance(open_model, OpenPath) and open_model.path is not None:
        open_path(open_model.path)
        return {
            "message": f"Opening path: {open_model.path}",
        }
    if isinstance(open_model, OpenUrl) and open_model.url is not None:
        open_url(open_model.url)
        return {
            "message": f"Opening URL: {open_model.url}",
        }
    raise HTTPException(
        status.HTTP_400_BAD_REQUEST,
        {"message": "No path or URL specified"},
    )


@app.post("/api/power/sleep", dependencies=[Depends(security_token)])
def send_power_sleep() -> dict[str, str]:
    """Send power sleep."""
    app.loop.create_task(
        schedule_power_event(2, sleep),
        name="Power Sleep",
    )
    return {"message": "Sleeping"}


@app.post("/api/power/hibernate", dependencies=[Depends(security_token)])
def send_power_hibernate() -> dict[str, str]:
    """Send power hibernate."""
    app.loop.create_task(
        schedule_power_event(2, hibernate),
        name="Power Hibernate",
    )
    return {"message": "Hibernating"}


@app.post("/api/power/restart", dependencies=[Depends(security_token)])
def send_power_restart() -> dict[str, str]:
    """Send power restart."""
    app.loop.create_task(
        schedule_power_event(2, restart),
        name="Power Restart",
    )
    return {"message": "Restarting"}


@app.post("/api/power/shutdown", dependencies=[Depends(security_token)])
def send_power_shutdown() -> dict[str, str]:
    """Send power shutdown."""
    app.loop.create_task(
        schedule_power_event(2, shutdown),
        name="Power Shutdown",
    )
    return {"message": "Shutting down"}


@app.post("/api/power/lock", dependencies=[Depends(security_token)])
def send_power_lock() -> dict[str, str]:
    """Send power lock."""
    app.loop.create_task(
        schedule_power_event(2, lock),
        name="Power Lock",
    )
    return {"message": "Locking"}


@app.post("/api/power/logout", dependencies=[Depends(security_token)])
def send_power_logout() -> dict[str, str]:
    """Send power logout."""
    app.loop.create_task(
        schedule_power_event(2, logout),
        name="Power Logout",
    )
    return {"message": "Logging out"}


@app.post("/api/update", dependencies=[Depends(security_token)])
def send_update(
    query_version: str = Query(..., alias="version")
) -> dict[str, dict[str, str | None] | str]:
    """Send update."""
    if (versions := version_update(query_version)) is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            {"message": "Invalid version"},
        )
    return {
        "message": "Updating the application",
        "versions": versions,
    }


@app.websocket("/api/websocket")
async def websocket_endpoint(websocket: WebSocket):
    """Websocket endpoint."""
    await websocket.accept()
    websocket_handler = WebSocketHandler(
        settings,
        app.data_update,
        app.listeners,
        websocket,
        app.callback_exit,
        app.callback_open_gui,
    )
    await websocket_handler.handler()


if "--no-frontend" not in sys.argv:
    try:
        # pylint: disable=import-error, import-outside-toplevel
        from systembridgefrontend import get_frontend_path

        frontend_path = get_frontend_path()
        logger.info("Serving frontend from: %s", frontend_path)
        app.mount(
            path="/",
            app=StaticFiles(directory=frontend_path),
            name="Frontend",
        )
    except (ImportError, ModuleNotFoundError) as error:
        logger.error("Frontend not found", exc_info=error)
