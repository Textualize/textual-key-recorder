"""A list for showing unknown key sequences."""

from .keys_display import KeysDisplay


class UnknownKeys(KeysDisplay):
    """A widget to show unknown key sequences."""

    BORDER_TITLE = "Unknown Sequences"
