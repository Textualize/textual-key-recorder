"""Provides a dialog for editing an annotation."""

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Button, TextArea


class DialogTextArea(TextArea):
    """A version of `TextArea` that's friendly to this dialog."""

    async def _on_key(self, event: Key) -> None:
        """Allow tab to move along the focus chain."""
        if event.key == "tab":
            event.prevent_default()
            self.screen.focus_next()


class Annotation(ModalScreen[str]):
    """A dialog for editing an annotation."""

    DEFAULT_CSS = """
    Annotation {
        align: center middle;
    }

    Vertical {
        width: 50%;
        height: 50%;
        border: panel cornflowerblue;
        padding: 1 2;
        background: $panel;
    }

    Horizontal {
        align: right middle;
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

    def __init__(self, key: str, annotation: str = "") -> None:
        """Initialise the annotation dialog.

        Args:
            annotation: The note to edit.
        """
        super().__init__()
        self._key = key
        self._annotation = annotation

    def compose(self) -> ComposeResult:
        with Vertical() as panel:
            panel.border_title = f"Annotation for {self._key}"
            yield DialogTextArea(self._annotation)
            with Horizontal():
                yield Button("Save", id="save")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        """Configure the dialog once mounted."""
        self.query_one(TextArea).show_line_numbers = False

    @on(Button.Pressed, "#save")
    def save(self) -> None:
        """Handle the save button."""
        self.dismiss(self.query_one(TextArea).text)

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        """Handle the cancel button."""
        self.app.pop_screen()
