"""Fixtures for testing."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from systembridgemodels.settings import Settings


@pytest.fixture(autouse=True)
def mock_settings() -> Generator[MagicMock, None, None]:
    """Mock settings."""
    with patch(
        "systembridgeshared.settings.Settings",
        autospec=True,
    ) as mocked_settings:
        settings = mocked_settings.return_value
        settings.data.return_value = Settings()

        yield settings


@pytest.fixture
def mock_server() -> Generator[MagicMock, None, None]:
    """Mock server."""
    with patch(
        "systembridgebackend.server.Server",
        autospec=True,
    ) as mocked_server:
        server = mocked_server.return_value

        yield server


@pytest.fixture
def mock_listeners() -> Generator[MagicMock, None, None]:
    """Mock listeners."""
    with patch(
        "systembridgebackend.modules.listeners.Listeners",
        autospec=True,
    ) as mocked_listeners:
        listeners = mocked_listeners.return_value

        yield listeners
