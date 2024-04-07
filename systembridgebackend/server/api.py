"""API."""

import asyncio
from collections.abc import Callable
from dataclasses import asdict, is_dataclass
import logging
import os
import sys
from typing import Any

from fastapi import Depends, FastAPI, Header, Query, WebSocket, status
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from systembridgebackend.handlers.media import get_directories, get_file_data
from systembridgeshared.common import asyncio_get_loop
from systembridgeshared.const import HEADER_TOKEN, QUERY_TOKEN
from systembridgeshared.settings import Settings

from .._version import __version__
from ..handlers.data import DataUpdate
from ..modules import MODULES
from ..modules.listeners import Listeners
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
    title="System Bridge Backend",
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
