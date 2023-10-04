"""The main screen for the application."""

from dataclasses import dataclass

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.events import Key
from textual.keys import KEY_TO_UNICODE_NAME, Keys
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Footer, Header, OptionList, Static
from textual.widgets.option_list import DuplicateID, Option, OptionDoesNotExist


class TestableKey(Option):
    """A class for holding details of a testable key."""

    def __init__(self, key: str) -> None:
        """Initialise the testable key.

        Args:
            key: The name of the key.
        """
        super().__init__(key, id=key)
        self.notes = ""
        """Holds user-entered notes about the key."""


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
        key: Key

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

        # If this is out first attempt at a focus switch don't switch but
        # record it's fine form now on.
        if event.key == "tab":
            self.tab_tested = True
            event.stop()
        elif event.key == "shift+tab":
            self.shift_tab_tested = True
            event.stop()


class Main(Screen):
    """The main screen of the application."""

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

        # Pull out the two lists.
        expected = self.query_one(ExpectedKeys)
        unexpected = self.query_one(UnexpectedKeys)
        triggered = self.query_one(TriggeredKeys)

        try:
            # Is the key in the list of expected keys?
            expected_key = expected.get_option(event.key.key)
        except OptionDoesNotExist:
            # It's not there, but it could have been triggered already, so
            # let's check that...
            try:
                _ = triggered.get_option(event.key.key)
            except OptionDoesNotExist:
                # It's not in the list that was triggered either; so that
                # suggests it's known, isn't expected, and we've not seen
                # it. Guess it's unexpected then!
                try:
                    unexpected.add_option(TestableKey(event.key.key))
                except DuplicateID:
                    pass
            return

        # If the key was expected...
        if expected_key is not None:
            try:
                # ...add it to the list of triggered keys.
                triggered.add_option(expected_key)
            except DuplicateID:
                # Oh, wait, we already know about it. Carry on.
                pass
            # Finally, remove it from the list of expected keys.
            expected.remove_option(event.key.key)
