"""display control DDC/CI handlers."""
from monitorcontrol.monitorcontrol import get_monitors

from systembridgemodels.modules.displays import InputSource, PowerMode

from ..modules.displays import vcpcode_volume


def set_brightness(
    monitor_id: int,
    brightness: int,
) -> None:
    """
    Set the brightness of a monitor.

    Args:
        monitor_id (int): The ID of the monitor to set the brightness for.
        brightness (int): The new brightness level, on a scale from 0 to 100.

    Raises:
        ValueError: If the brightness value is not in the range [0, 100].
    """
    monitors = get_monitors()
    with monitors[monitor_id] as monitor:
        monitor.set_luminance(brightness)


def set_contrast(
    monitor_id: int,
    contrast: int,
) -> None:
    """
    Set the contrast of a monitor.

    Args:
        monitor_id (int): The ID of the monitor to set the contrast for.
        contrast (int): The new contrast level, on a scale from 0 to 100.

    Raises:
        ValueError: If the contrast value is not in the range [0, 100].
    """
    monitors = get_monitors()
    with monitors[monitor_id] as monitor:
        monitor.set_contrast(contrast)


def set_volume(
    monitor_id: int,
    volume: int,
) -> None:
    """
    Set the volume of a monitor.

    Args:
        monitor_id (int): The ID of the monitor to set the volume for.
        volume (int): The new volume level, on a scale from 0 to 100.

    Raises:
        ValueError: If the volume value is not in the range [0, 100].
    """
    monitors = get_monitors()
    with monitors[monitor_id] as monitor:
        monitor._set_vcp_feature(vcpcode_volume, volume)  # pylint: disable=protected-access


def set_power_state(
    monitor_id: int,
    power_state: PowerMode | int | str,
) -> None:
    """
    Set the power state of a monitor.

    Args:
        monitor_id (int): The ID of the monitor to set the power state for.
        power_state (int | str | PowerMode): The new power state, can be an integer,
            a string representing the power mode, or a `PowerMode` enum value.
    """
    monitors = get_monitors()
    with monitors[monitor_id] as monitor:
        monitor.set_power_mode(power_state)


def set_input_source(
    monitor_id: int,
    input_source: InputSource | int | str,
) -> None:
    """
    Set the input source of a monitor.

    Args:
        monitor_id: The ID of the monitor to set the input source for.
        input_source: The new input source, which can be an integer, string, or `InputSource` enum value.

    Raises:
        ValueError: If the input source is not recognized by the monitor.
    """
    monitors = get_monitors()
    with monitors[monitor_id] as monitor:
        monitor.set_input_source(input_source)
