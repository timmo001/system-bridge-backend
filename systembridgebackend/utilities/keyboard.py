"""Keyboard Utilities."""
from keyboard import press_and_release, write


def keyboard_keypress(key: str) -> None:
    """Press a keyboard key."""
    press_and_release(key)


def keyboard_text(text: str) -> None:
    """Type text."""
    write(text)
