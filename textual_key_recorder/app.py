"""The main application class."""

from textual.app import App

from .screens import Main


class TextualKeyRecorder(App[None]):
    """Application class for the Textual key recorder."""

    TITLE = "Textual Key Recorder"

    def on_mount(self) -> None:
        """Set up the application once the DOM is ready."""
        self.push_screen(Main())
