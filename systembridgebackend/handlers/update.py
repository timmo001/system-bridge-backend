"""Update handlers."""

from systembridgeshared.update import Update


def version_update(
    version: str,
) -> dict[str, str | None]:
    """Handle the update request."""
    versions = Update().update(
        version,
        wait=False,
    )
    return versions
