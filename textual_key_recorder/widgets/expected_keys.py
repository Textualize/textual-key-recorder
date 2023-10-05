"""A list for showing expected keys."""

from textual.keys import KEY_TO_UNICODE_NAME, Keys

from .keys_display import KeysDisplay, TestableKey


class ExpectedKeys(KeysDisplay):
    """A widget to show the keys we expect to encounter."""

    BORDER_TITLE = "Expected Keys"

    def __init__(self) -> None:
        """Initialise the widget."""
        super().__init__(
            *[
                TestableKey(key)
                for key in sorted(
                    set(key.value for key in Keys) | set(KEY_TO_UNICODE_NAME.keys())
                )
                if not key.startswith("<")
            ],
        )
