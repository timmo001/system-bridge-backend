"""Main."""

import logging

import typer

from systembridgebackend import Application
from systembridgeshared.logger import setup_logger
from systembridgeshared.settings import Settings

app = typer.Typer()


@app.command(name=None, short_help="Main Application")
def main(
    init: bool = typer.Option(False, "--init", help="Initialise"),
    no_frontend: bool = typer.Option(False, "--no-frontend", help="No Frontend"),
) -> None:
    """Run the main application."""
    settings = Settings()

    logger = setup_logger(settings.data.log_level, "systembridgebackend")
    logging.getLogger("zeroconf").setLevel(logging.ERROR)

    try:
        Application(
            settings,
            init=init,
            no_frontend=no_frontend,
        )
    except Exception as exception:  # pylint: disable=broad-except
        logger.fatal("Unhandled error in application", exc_info=exception)


if __name__ == "__main__":
    app()
