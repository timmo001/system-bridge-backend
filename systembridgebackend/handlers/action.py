"""Action Utilities."""

from typing import Any

from systembridgeconnector.exceptions import (
    AuthenticationException,
    ConnectionErrorException,
)
from systembridgeconnector.http_client import HTTPClient
from systembridgemodels.action import Action
from systembridgeshared.base import Base
from systembridgeshared.settings import Settings


class ActionHandler(Base):
    """Handle actions."""

    def __init__(
        self,
        settings: Settings,
    ) -> None:
        """Initialise the action handler."""
        super().__init__()
        self._settings = settings

    async def handle(
        self,
        action: Action,
    ) -> None:
        """Handle an action."""
        self._logger.info("Action: %s", action)
        if action.command == "api" and action.data is not None:
            await self.api_action(action.data)
        else:
            self._logger.info("Unknown action: %s", action)

    async def api_action(
        self,
        data: dict[str, Any],
    ) -> Any:
        """Handle an API action."""
        self._logger.info("API Action: %s", data)

        api_port = self._settings.data.api.port
        token = self._settings.data.api.token
        if api_port is None or token is None:
            self._logger.warning("API not configured")
            return

        http_client = HTTPClient(
            "localhost",
            api_port,
            token,
        )
        method = str(data["method"]).upper()
        try:
            if method == "DELETE":
                return await http_client.delete(
                    f"/api/{data['endpoint']}",
                    data.get("body"),
                )
            if method == "GET":
                return await http_client.get(f"/api/{data['endpoint']}")
            if method == "POST":
                return await http_client.post(
                    f"/api/{data['endpoint']}",
                    data.get("body"),
                )
            if method == "PUT":
                return await http_client.put(
                    f"/api/{data['endpoint']}",
                    data.get("body"),
                )
            self._logger.warning("Unknown API method: %s", method)
            return None
        except AuthenticationException as error:
            self._logger.warning("API authentication error", exc_info=error)
        except ConnectionErrorException as error:
            self._logger.warning("API connection error", exc_info=error)
