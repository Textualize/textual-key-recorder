"""The main screen for the application."""

from __future__ import annotations

from json import dumps, loads, JSONDecodeError
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Key
from textual.message import Message
from textual.reactive import var
from textual.screen import Screen
from textual.widgets import Footer, Header

from textual_fspicker import FileOpen, FileSave, Filters

from ..dialogs import YesNo
from ..widgets import (
    KeyInput,
    KeysDisplay,
    ExpectedKeys,
    TriggeredKeys,
    UnexpectedKeys,
    TestableKey,
)


class AdminArea(Horizontal):
    """The area of the application where admin tasks can take place."""

    BINDINGS = [
        Binding("ctrl+l", "load", "Load progress"),
        Binding("ctrl+s", "save", "Save progress"),
    ]

    progress_file: var[Path | None] = var(None)
    """The file where progress is recorded."""

    dirty: var[bool] = var(False)
    """Is the data dirty?"""

    FILE_EXTENSION = ".tkrec"
    """The extension used for the files saved by this application."""

    FILTERS = Filters(
        (
            "Textual Keys Recording",
            lambda p: p.suffix.lower() == AdminArea.FILE_EXTENSION,
        )
    )
    """The filters to use for the file dialogs."""

    class DataLoaded(Message):
        """Message posted when fresh data is loaded."""

    def compose(self) -> ComposeResult:
        """Compose the child widgets."""
        yield ExpectedKeys()
        with Vertical():
            yield TriggeredKeys()
            yield UnexpectedKeys()

    def to_json(self) -> dict[str, list[dict[str, str]]]:
        """Get the state of the screen as a json-friendly data structure.

        Returns:
            A json-friendly structure of the data.
        """
        return {
            "expected": self.query_one(ExpectedKeys).to_json(),
            "unexpected": self.query_one(UnexpectedKeys).to_json(),
            "triggered": self.query_one(TriggeredKeys).to_json(),
        }

    def _save_data(self, save_file: Path | None) -> None:
        """Save the current state to the given file.

        Args:
            save_file: The file to save to, or `None` if no save should
                happen.
        """
        if save_file is not None:
            save_file = save_file.with_suffix(self.FILE_EXTENSION)
            self.progress_file = save_file
            save_file.write_text(dumps(self.to_json(), indent=4))
            self.dirty = False
            self.notify(str(save_file), title="Saved")

    def action_save(self) -> None:
        """Save the current progress."""
        if self.progress_file is None:
            self.app.push_screen(
                FileSave(filters=self.FILTERS), callback=self._save_data
            )
        else:
            self._save_data(self.progress_file)

    def _load_data(self, load_file: Path | None) -> None:
        """Load state from the given file.

        Args:
            load_file: The file to load from, or `None` if no load is to
                happen.
        """
        if load_file is not None:

            def error():
                self.notify(
                    "Not a valid key recording session file.",
                    title="Error loading file",
                    severity="error",
                    timeout=6,
                )

            try:
                data = loads(load_file.read_text())
            except JSONDecodeError:
                error()
                return
            if all(
                required in data for required in ("expected", "unexpected", "triggered")
            ):
                self.progress_file = load_file
                self.query_one(ExpectedKeys).from_json(data["expected"])
                self.query_one(UnexpectedKeys).from_json(data["unexpected"])
                self.query_one(TriggeredKeys).from_json(data["triggered"])
                self.post_message(self.DataLoaded())
            else:
                error()

    def _initiate_load(self, really_load: bool = True) -> None:
        """Core file loading method.

        Args:
            really_load: Flag to say if we should really load the file.
        """
        if really_load:
            self.app.push_screen(
                FileOpen(filters=self.FILTERS), callback=self._load_data
            )

    def action_load(self) -> None:
        """Start the process of loading a progress file."""
        if self.dirty:
            self.app.push_screen(
                YesNo("You have unsaved data, do you really want to load?"),
                callback=self._initiate_load,
            )
        else:
            self._initiate_load()

    def _refresh_subtitle(self) -> None:
        """Refresh the subtitle of the app."""
        self.app.sub_title = (
            "Untitled" if self.progress_file is None else str(self.progress_file)
        ) + (" (unsaved)" if self.dirty else "")

    def _watch_progress_file(self) -> None:
        """Refresh when the progress file name changes."""
        self._refresh_subtitle()

    def _watch_dirty(self) -> None:
        """Refresh when the dirty flag changes."""
        self._refresh_subtitle()


class Main(Screen):
    """The main screen of the application."""

    def compose(self) -> ComposeResult:
        """Compose the child widgets."""
        yield Header()
        yield KeyInput()
        yield AdminArea()
        yield Footer()

    @on(KeysDisplay.NotesUpdated)
    def _mark_dirty(self) -> None:
        """Mark the data as dirty in response to events."""
        self.query_one(AdminArea).dirty = True

    @on(AdminArea.DataLoaded)
    def _reset_recorder(self) -> None:
        """Configure things after new data has been loaded."""
        triggered = self.query_one(TriggeredKeys)
        self.query_one(KeyInput).tab_tested = "tab" in triggered
        self.query_one(KeyInput).shift_tab_tested = "shift+tab" in triggered

    @on(KeyInput.Triggered)
    def mark_key_as_triggered(self, event: KeyInput.Triggered):
        """Handle a key being triggered.

        Args:
            event: The key trigger event.
        """

        # Pull out the various lists.
        expected = self.query_one(ExpectedKeys)
        unexpected = self.query_one(UnexpectedKeys)
        triggered = self.query_one(TriggeredKeys)

        def _add(key: Key | TestableKey, target: KeysDisplay) -> None:
            target.add_option(key if isinstance(key, TestableKey) else TestableKey(key))
            target.action_last()
            self._mark_dirty()

        # First off, get the key that was triggered.
        triggered_key = event.key

        # Figure out where the key should land, if at all.
        if triggered_key in expected:
            # It's in the expected list, so move it over to the triggered list.
            _add(expected.get_option(triggered_key.key), triggered)
            expected.remove_option(triggered_key.key)
        elif triggered_key.is_printable:
            # Printable keys that we weren't expecting are treated as kind
            # of expected, so if it isn't in the triggered list yet, add it
            # now.
            if triggered_key not in triggered:
                _add(triggered_key, triggered)
        elif triggered_key not in triggered and triggered_key not in unexpected:
            # It's not expected and hasn't been triggered, and so far hasn't
            # landed in the unexpected list; so add it now.
            _add(triggered_key, unexpected)
