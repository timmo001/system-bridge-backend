"""Test __init__ module."""

from unittest.mock import MagicMock

from systembridgebackend.__init__ import Application


def test_application(
    mock_listeners: MagicMock,
    mock_server: MagicMock,
    mock_settings: MagicMock,
):
    """Test the Application class."""
    Application(
        mock_settings,
        init=False,
        no_frontend=False,
    )
