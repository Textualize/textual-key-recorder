"""A list for showing unexpected keys."""

from .keys_display import KeysDisplay


class UnexpectedKeys(KeysDisplay):
    """A widget to show the keys we didn't expect to encounter."""

    BORDER_TITLE = "Unexpected Keys"
