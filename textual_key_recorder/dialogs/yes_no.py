"""Provides a simple yes/no dialog."""

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class YesNo(ModalScreen[bool]):
    """A simple yes/no dialog."""

    DEFAULT_CSS = """
    YesNo {
        align: center middle;
    }

    Vertical {
        width: auto;
        height: auto;
        border: thick $accent;
        padding: 1 2;
        background: $panel;
    }

    Horizontal {
        align: right middle;
        width: auto;
        height: auto;
        margin-top: 1;
    }

    Button {
        margin-left: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "app.pop_screen", show=False),
    ]

    def __init__(self, question: str = "") -> None:
        """Initialise the question dialog.

        Args:
            question: The question to ask.
        """
        super().__init__()
        self._question = question

    def compose(self) -> ComposeResult:
        """Compose the content of the dialog."""
        with Vertical():
            yield Label(self._question)
            with Horizontal():
                yield Button("Yes", id="yes")
                yield Button("No", id="no")

    @on(Button.Pressed)
    def decision(self, event: Button.Pressed) -> None:
        """Handle the user's decision.

        Args:
            event: The button press event that is the decision.
        """
        self.dismiss(event.button.id == "yes")
