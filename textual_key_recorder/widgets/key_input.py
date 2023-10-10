"""A widget for grabbing key input data."""

from dataclasses import dataclass

from textual._xterm_parser import XTermParser
from textual.events import Key
from textual.message import Message
from textual.widgets import Static


class KeyInput(Static, can_focus=True):
    """The widget where a key should be input."""

    BORDER_TITLE = "Key Press"
    BORDER_SUBTITLE = "Focus this widget to test a key"

    DEFAULT_CSS = """
    KeyInput {
        border: panel cornflowerblue 50%;
        height: 5;
        padding: 1;
        text-align: center;
        width: 1fr;
    }

    KeyInput:focus {
        border: panel cornflowerblue;
    }
    """

    @dataclass
    class Triggered(Message):
        """Event raised when a key is triggered."""

        key: Key
        """The key that was triggered."""

    @dataclass
    class Unknown(Message):
        """Event raised when an unknown sequence comes in."""

        sequence: str
        """The sequence that came in."""

    def __init__(self) -> None:
        """Initialise the widget."""
        super().__init__("Press a key to test...")
        self.tab_tested = False
        self.shift_tab_tested = False

    def _unknown_sequence(self, sequence: str) -> None:
        """Report an unknown sequence.

        Args:
            sequence: The unknown sequence to report.
        """
        self.post_message(self.Unknown(repr(sequence)[1:-1]))

    def on_focus(self) -> None:
        """Hook into the unknown sequence code while we have focus.."""
        XTermParser._reissued_sequence_debug_book = self._unknown_sequence

    def on_blur(self) -> None:
        """Unhook from the unknown sequence capture when focus is lost."""
        XTermParser._reissued_sequence_debug_book = None

    def on_key(self, event: Key):
        """Handle keystrokes.

        Args:
            event: The key event to handle.
        """
        # Just let focus switching do its thing if we've already triggered it.
        if (event.key == "tab" and self.tab_tested) or (
            event.key == "shift+tab" and self.shift_tab_tested
        ):
            return

        self.update(f"{event!r}")
        self.post_message(self.Triggered(event))

        # If this is our first attempt at a focus switch don't switch but
        # record it's fine form now on.
        if event.key == "tab":
            self.tab_tested = True
            event.stop()
        elif event.key == "shift+tab":
            self.shift_tab_tested = True
            event.stop()
