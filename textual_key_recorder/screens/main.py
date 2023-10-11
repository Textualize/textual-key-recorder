"""The main screen for the application."""

from __future__ import annotations

from json import JSONDecodeError, dumps, loads
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Key
from textual.message import Message
from textual.reactive import var
from textual.screen import Screen
from textual.widgets import Button, Footer, Header
from textual_fspicker import FileOpen, FileSave, Filters

from ..dialogs import YesNo
from ..widgets import (
    Environment,
    ExpectedKeys,
    KeyInput,
    KeysDisplay,
    Notepad,
    TestableKey,
    TriggeredKeys,
    UnexpectedKeys,
    UnknownKeys,
)


class AdminArea(Horizontal):
    """The area of the application where admin tasks can take place."""

    DEFAULT_CSS = """
    AdminArea {
        margin-top: 1;
        margin-bottom: 1;
    }

    Environment {
        margin-top: 1;
    }

    UnknownKeys {
        margin-top: 1;
    }

    ExpectedKeys {
        height: 3fr;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+l", "load", "Load progress"),
        Binding("ctrl+s", "save", "Save progress"),
        Binding("ctrl+q", "quit_recorder", "Quit"),
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
        with Vertical():
            yield ExpectedKeys()
            yield Notepad()
        with Vertical():
            with Horizontal():
                yield TriggeredKeys()
                with Vertical():
                    yield UnexpectedKeys()
                    yield UnknownKeys()
            yield Environment()

    def to_json(self) -> dict[str, dict[str, str] | list[dict[str, str]] | str]:
        """Get the state of the screen as a json-friendly data structure.

        Returns:
            A json-friendly structure of the data.
        """
        return {
            "environment": self.query_one(Environment).to_json(),
            "expected": self.query_one(ExpectedKeys).to_json(),
            "unexpected": self.query_one(UnexpectedKeys).to_json(),
            "unknown": self.query_one(UnknownKeys).to_json(),
            "triggered": self.query_one(TriggeredKeys).to_json(),
            "notes": self.query_one(Notepad).text,
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
                required in data
                for required in ("expected", "unexpected", "triggered", "unknown")
            ):
                self.progress_file = load_file
                self.query_one(ExpectedKeys).from_json(data["expected"])
                self.query_one(UnexpectedKeys).from_json(data["unexpected"])
                self.query_one(TriggeredKeys).from_json(data["triggered"])
                self.query_one(UnknownKeys).from_json(data["unknown"])
                self.query_one(Notepad).load_text(data.get("notes", ""))
                self.post_message(self.DataLoaded())
                if not self.query_one(Environment).is_similar(
                    data.get("environment", {})
                ):
                    self.notify(
                        "Data loaded for a dissimilar environment!",
                        severity="warning",
                        timeout=8,
                    )
                self.dirty = False
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

    def _really_quit(self, confirmed: bool) -> None:
        """Unconditionally exit the application.

        Args:
            confirmed: Was the quit confirmed by the user?
        """
        if confirmed:
            self.app.exit()

    def action_quit_recorder(self) -> None:
        """Quit the recorder."""
        if self.dirty:
            self.app.push_screen(
                YesNo("You have unsaved data, do you really want to quit?"),
                callback=self._really_quit,
            )
        else:
            self.app.exit()

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


class Toolbar(Vertical):
    """Toolbar widget."""

    DEFAULT_CSS = """
    Toolbar {
        border: round cornflowerblue 50%;
        background: $panel;
        width: auto;
        height: auto;
    }

    Toolbar Button, Toolbar Button:hover, Toolbar Button.-active {
        border: none;
        height: auto;
    }
    """

    BINDINGS = [
        Binding("up", "focus_previous"),
        Binding("down", "focus_next"),
    ]


class Main(Screen):
    """The main screen of the application."""

    CSS = """
    #inputs {
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the child widgets."""
        yield Header()
        with Horizontal(id="inputs"):
            yield KeyInput()
            with Toolbar():
                yield Button("Load", id="load")
                yield Button("Save", id="save")
                yield Button("Quit", id="quit_recorder")
        yield AdminArea()
        yield Footer()

    @on(KeysDisplay.NotesUpdated)
    @on(Notepad.Changed)
    def _mark_dirty(self) -> None:
        """Mark the data as dirty in response to events."""
        self.query_one(AdminArea).dirty = True

    @on(AdminArea.DataLoaded)
    def _reset_recorder(self) -> None:
        """Configure things after new data has been loaded."""
        triggered = self.query_one(TriggeredKeys)
        self.query_one(KeyInput).tab_tested = "tab" in triggered
        self.query_one(KeyInput).shift_tab_tested = "shift+tab" in triggered

    def _add(self, key: str | Key | TestableKey, target: KeysDisplay) -> None:
        """Add a key to the target list.

        Args:
            key: The key to record.
            target: The list to record the key in.
        """
        target.add_option(
            key if isinstance(key, TestableKey) else TestableKey(key)
        ).refresh_count().action_last()
        self._mark_dirty()

    @on(KeyInput.Triggered)
    def mark_key_as_triggered(self, event: KeyInput.Triggered) -> None:
        """Handle a key being triggered.

        Args:
            event: The key trigger event.
        """

        # Pull out the various lists.
        expected = self.query_one(ExpectedKeys)
        unexpected = self.query_one(UnexpectedKeys)
        triggered = self.query_one(TriggeredKeys)

        # First off, get the key that was triggered.
        triggered_key = event.key

        # Figure out where the key should land, if at all.
        if triggered_key in expected:
            # It's in the expected list, so move it over to the triggered list.
            self._add(expected.get_option(triggered_key.key), triggered)
            expected.remove_option(triggered_key.key).refresh_count()
        elif triggered_key.is_printable:
            # Printable keys that we weren't expecting are treated as kind
            # of expected, so if it isn't in the triggered list yet, add it
            # now.
            if triggered_key not in triggered:
                self._add(triggered_key, triggered)
        elif triggered_key not in triggered and triggered_key not in unexpected:
            # It's not expected and hasn't been triggered, and so far hasn't
            # landed in the unexpected list; so add it now.
            self._add(triggered_key, unexpected)

    @on(KeyInput.Unknown)
    def record_unknown_key(self, event: KeyInput.Unknown) -> None:
        """Record an unknown key.

        Args:
            event: The unknown key event.
        """
        unknown = self.query_one(UnknownKeys)
        if event.sequence not in unknown:
            self._add(event.sequence, unknown)
        self.app.bell()
        self.notify(
            event.sequence,
            title="Unknown sequence received",
            severity="warning",
            timeout=10,
        )

    @on(Button.Pressed)
    async def toolbar_button(self, event: Button.Pressed) -> None:
        """Handle toolbar buttons.

        Args:
            event: The button press event.
        """
        if event.control.id and isinstance(event.control.parent, Toolbar):
            await self.query_one(AdminArea).run_action(event.control.id)
