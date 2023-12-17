"""Main."""
import logging

from systembridgeshared.logger import setup_logger
from systembridgeshared.settings import Settings
import typer

from . import Application

app = typer.Typer()

settings = Settings()

LOG_LEVEL = settings.data.log_level
logger = setup_logger(LOG_LEVEL, "system-bridge")
logging.getLogger("zeroconf").setLevel(logging.ERROR)


@app.command(name=None, short_help="Main Application")
def main(
    init: bool = typer.Option(False, "--init", help="Initialise"),
    no_frontend: bool = typer.Option(False, "--no-frontend", help="No Frontend"),
) -> None:
    """Main Application."""
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
