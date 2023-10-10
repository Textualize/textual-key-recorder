"""Notepad widget for the general session notes."""

from textual.widgets import TextArea


class Notepad(TextArea):
    """A notepad widget for the key recording session data."""

    BORDER_TITLE = "Notepad"

    DEFAULT_CSS = """
    Notepad {
        border: panel cornflowerblue 50%;
        height: 1fr;
    }

    Notepad:focus {
        border: panel cornflowerblue;
    }
    """

    def on_mount(self) -> None:
        """Configure the notepad once mounted in the DOM."""
        self.show_line_numbers = False
