"""Notepad widget for the general session notes."""

from textual.events import Key
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

    async def _on_key(self, event: Key) -> None:
        """Allow tab to move along the focus chain."""
        if event.key == "tab":
            event.prevent_default()
            self.screen.focus_next()
