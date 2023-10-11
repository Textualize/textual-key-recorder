"""Provides the base class for a widget that displays keys."""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import cast

from rich.emoji import Emoji
from textual.binding import Binding
from textual.events import Key
from textual.message import Message
from textual.widgets import OptionList
from textual.widgets.option_list import Option, OptionDoesNotExist
from typing_extensions import Final, Self

from ..dialogs import Annotation


class TestableKey(Option):
    """A class for holding details of a testable key."""

    NOTE_ICON: Final[str] = Emoji.replace(":paperclip:")
    """The icon to use to indicate a key has a note attached."""

    def __init__(self, key: str | Key, notes: str = "") -> None:
        """Initialise the testable key.

        Args:
            key: The name of the key.
        """
        key = key if isinstance(key, str) else key.key
        super().__init__(key, id=key)
        self._notes = notes
        """Holds user-entered notes about the key."""

    @property
    def notes(self) -> str:
        """The notes for the key."""
        return self._notes

    @notes.setter
    def notes(self, notes: str) -> None:
        """Set the notes for the key."""
        self._notes = notes
        assert self.id is not None
        self.set_prompt(f"{self.id} {self.NOTE_ICON}" if notes.strip() else self.id)

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
        border: panel cornflowerblue 50%;
        width: 1fr;
        height: 1fr;
    }

    KeysDisplay:focus {
        border: panel cornflowerblue;
    }
    """

    BINDINGS = [Binding("enter", "annotate", "Annotate Key")]

    @dataclass
    class NotesUpdated(Message):
        """Message posted when the notes of a key are modified."""

        keys_list: KeysDisplay
        """The list that handled the update."""
        key: TestableKey
        """The key that was updated."""

        @property
        def control(self) -> KeysDisplay:
            """The control sending the message."""
            return self.keys_list

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
        self.clear_options().add_options(
            TestableKey.from_json(key) for key in data
        ).refresh_count()

    def _update_notes(self, key: TestableKey, notes: str) -> None:
        """Update the notes for the given key.

        Args:
            key: The key to update.
            notes: The notes to update the key with.
        """
        if key.notes != notes:
            self.post_message(self.NotesUpdated(self, key))
            key.notes = notes
            self._refresh_content_tracking(force=True)
            self.refresh()

    def action_annotate(self) -> None:
        """Annotate the current key."""
        if self.highlighted is not None:
            key = self.get_option_at_index(self.highlighted)
            assert isinstance(key, TestableKey) and key.id is not None
            self.app.push_screen(
                Annotation(key.id, key.notes), callback=partial(self._update_notes, key)
            )

    def get_option(self, option_id: str) -> TestableKey:
        """Override to cast the return type to the `Option` subclass.

        Args:
            option_id: The ID of the option to get.

        Returns:
            The testable key with that ID.
        """
        return cast(TestableKey, super().get_option(option_id))

    def on_mount(self) -> None:
        """Configure the list once the DOM is ready."""
        self.refresh_count()

    def refresh_count(self) -> Self:
        """Refresh the count of keys in the list as shown in the border."""
        if self.BORDER_TITLE:
            self.border_title = f"{self.BORDER_TITLE} ({self.option_count})"
        return self
