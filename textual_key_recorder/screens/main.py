"""The main screen for the application."""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from json import dumps, loads
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Key
from textual.keys import KEY_TO_UNICODE_NAME, Keys
from textual.message import Message
from textual.reactive import var
from textual.screen import Screen
from textual.widgets import Footer, Header, OptionList, Static
from textual.widgets.option_list import Option, OptionDoesNotExist

from textual_fspicker import FileOpen, FileSave

from ..dialogs import Annotation


class TestableKey(Option):
    """A class for holding details of a testable key."""

    def __init__(self, key: str | Key, notes: str = "") -> None:
        """Initialise the testable key.

        Args:
            key: The name of the key.
        """
        key = key if isinstance(key, str) else key.key
        super().__init__(key, id=key)
        self.notes = notes
        """Holds user-entered notes about the key."""

    def to_json(self) -> dict[str, str]:
        """Get the key data as a json-friendly data.

        Returns:
            The key data as json-friendly data.
        """
        assert self.id is not None
        return {"key": self.id, "notes": self.notes}

    @classmethod
    def from_json(cls, data: dict[str, str]) -> TestableKey:
        """Get a new `TestableKey` instance from json-friendly data.

        Args:
            data: The data to make the instance from.

        Returns:
            A fresh instance of `TestableKey`.
        """
        key = cls(data["key"])
        key.notes = data.get("notes", "")
        return key


class KeysDisplay(OptionList):
    """Base class for the key displays"""

    DEFAULT_CSS = """
    KeysDisplay {
        margin-top: 1;
        border: panel cornflowerblue 50%;
        width: 1fr;
        height: 1fr;
    }

    KeysDisplay:focus {
        border: panel cornflowerblue;
    }
    """

    BINDINGS = [Binding("enter", "annotate", "Annotate Key")]

    def __contains__(self, key: str | Key) -> bool:
        """Is the given key in this list?

        Args:
            key: The key to test for.
        """
        try:
            _ = self.get_option(key if isinstance(key, str) else key.key)
        except OptionDoesNotExist:
            return False
        return True

    def to_json(self) -> list[dict[str, str]]:
        """Get the keys in the list as json-friendly data.

        Returns:
            A json-friendly version of the data in the list.
        """
        return [key.to_json() for key in self._contents if isinstance(key, TestableKey)]

    def from_json(self, data: list[dict[str, str]]) -> None:
        """Set the content of the list to the content of the given json-friendly data.

        Args:
            data: The data to load into the list.
        """
        self.clear_options().add_options(TestableKey.from_json(key) for key in data)

    def _update_notes(self, key: TestableKey, notes: str) -> None:
        """Update the notes for the given key.

        Args:
            key: The key to update.
            notes: The notes to update the key with.
        """
        key.notes = notes

    def action_annotate(self) -> None:
        """Annotate the current key."""
        if self.highlighted is not None:
            key = self.get_option_at_index(self.highlighted)
            assert isinstance(key, TestableKey) and key.id is not None
            self.app.push_screen(
                Annotation(key.id, key.notes), callback=partial(self._update_notes, key)
            )


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


class TriggeredKeys(KeysDisplay):
    """A widget to show the keys that have been triggered."""

    BORDER_TITLE = "Triggered Keys"


class UnexpectedKeys(KeysDisplay):
    """A widget to show the keys we didn't expect to encounter."""

    BORDER_TITLE = "Unexpected Keys"


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

    def __init__(self) -> None:
        """Initialise the widget."""
        super().__init__("Press a key to test...")
        self.tab_tested = False
        self.shift_tab_tested = False

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


class Main(Screen):
    """The main screen of the application."""

    BINDINGS = [
        Binding("ctrl+l", "load", "Load progress"),
        Binding("ctrl+s", "save", "Save progress"),
    ]

    progress_file: var[Path | None] = var(None)
    """The file where progress is recorded."""

    def compose(self) -> ComposeResult:
        """Compose the child widgets."""
        yield Header()
        yield KeyInput()
        with Horizontal():
            yield ExpectedKeys()
            with Vertical():
                yield TriggeredKeys()
                yield UnexpectedKeys()
        yield Footer()

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

        # First off, get the key that was triggered.
        triggered_key = event.key

        # Figure out where the key should land, if at all.
        if triggered_key in expected:
            # It's in the expected list, so move it over to the triggered list.
            expected.remove_option(triggered_key.key)
            triggered.add_option(TestableKey(triggered_key))
        elif triggered_key.is_printable:
            # Printable keys that we weren't expecting are treated as kind
            # of expected, so if it isn't in the triggered list yet, add it
            # now.
            if triggered_key not in triggered:
                triggered.add_option(TestableKey(triggered_key))
        elif triggered_key not in triggered and triggered_key not in unexpected:
            # It's not expected and hasn't been triggered, and so far hasn't
            # landed in the unexpected list; so add it now.
            unexpected.add_option(TestableKey(triggered_key))

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
            self.progress_file = save_file
            save_file.write_text(dumps(self.to_json(), indent=4))
            self.notify(str(save_file), title="Saved")

    def action_save(self) -> None:
        """Save the current progress."""
        if self.progress_file is None:
            self.app.push_screen(FileSave(), callback=self._save_data)
        else:
            self._save_data(self.progress_file)

    def _load_data(self, load_file: Path | None) -> None:
        """Load state from the given file.

        Args:
            load_file: The file to load from, or `None` if no load is to
                happen.
        """
        if load_file is not None:
            # TODO: Error checking.
            data = loads(load_file.read_text())
            self.progress_file = load_file
            self.query_one(ExpectedKeys).from_json(data["expected"])
            self.query_one(UnexpectedKeys).from_json(data["unexpected"])
            self.query_one(TriggeredKeys).from_json(data["triggered"])
            self.query_one(KeyInput).tab_tested = "tab" in self.query_one(TriggeredKeys)
            self.query_one(KeyInput).shift_tab_tested = "shift+tab" in self.query_one(
                TriggeredKeys
            )

    def action_load(self) -> None:
        """Load a progress file."""
        self.app.push_screen(FileOpen(), callback=self._load_data)

    def _watch_progress_file(self) -> None:
        """Update the subtitle of the app when the progress file changes."""
        self.app.sub_title = (
            "Untitled" if self.progress_file is None else str(self.progress_file)
        )
