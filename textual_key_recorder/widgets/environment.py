"""A widget for holding and displaying environmental information."""

from __future__ import annotations

import os
import platform

from textual import __version__
from textual.widgets import DataTable


def _guess_term() -> str:
    """Try and guess which terminal is being used.

    Returns:
        The best guess at the name of the terminal.
    """

    # Look in a couple of generic locations for the name of the terminal.
    term_program = os.environ.get("TERM_PROGRAM") or os.environ.get("TERMINAL_NAME")

    if term_program is None:
        # Seems we couldn't get it that way. Let's check for some of the
        # more common terminal signatures.
        if "ALACRITTY_WINDOW_ID" in os.environ:
            term_program = "Alacritty"
        elif "KITTY_PID" in os.environ:
            term_program = "Kitty"
        elif "WT_SESSION" in os.environ:
            term_program = "Windows Terminal"
        elif "INSIDE_EMACS" in os.environ and os.environ["INSIDE_EMACS"]:
            term_program = (
                f"GNU Emacs {' '.join(os.environ['INSIDE_EMACS'].split(','))}"
            )
        elif "JEDITERM_SOURCE_ARGS" in os.environ:
            term_program = "PyCharm"

    else:
        # See if we can pull out some sort of version information too.
        term_version = os.environ.get("TERM_PROGRAM_VERSION") or os.environ.get(
            "TERMINAL_VERSION_STRING"
        )
        if term_version is not None:
            term_program = f"{term_program} ({term_version})"

    # Seems we can't work this out.
    if term_program is None:
        term_program = "*Unknown*"

    # Check for running under screen. As you look at this you might think
    # "what about tmux too?" -- good point; but we'll be picking up tmux as
    # the terminal type, because of how it takes over TERM_PROGRAM.
    if "STY" in os.environ:
        term_program += " (inside screen)"

    return term_program


class Environment(DataTable):
    """Widget that holds and shows the test environment details."""

    BORDER_TITLE = "Environment"

    DEFAULT_CSS = """
    Environment {
        height: auto;
        border: panel cornflowerblue 50%;
        color: $text 50%;
        scrollbar-gutter: stable;
    }

    Environment > .datatable--header {
        color: $text 50%;
    }

    Environment:focus {
        border: panel cornflowerblue;
        color: $text;
    }

    Environment:focus > .datatable--header {
        color: $text;
    }
    """

    def on_mount(self) -> None:
        """Configure the environment display once the DOM is ready."""
        self.cursor_type = "none"
        self.add_column("Name", key="name")
        self.add_column("Value", key="value")
        self.add_row("OS System", platform.system())
        self.add_row("OS Release", platform.release())
        self.add_row("OS Version", platform.version())
        self.add_row("Textual", __version__)
        self.add_row("Terminal", _guess_term())

    def to_json(self) -> dict[str, str]:
        """Get the environment information as json-friendly data.

        Returns:
            The environment data as json-friendly data.
        """
        return {
            "os_system": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "textual": __version__,
            "terminal": _guess_term(),
        }

    def is_similar(self, compare: dict[str, str]) -> bool:
        """Is the current environment the similar to another environment?

        Args:
            compare: The environment to compare to the current one.

        Returns:
            `True` if they're similar, `False` if different.
        """
        current = self.to_json()
        return all(current[key] == compare[key] for key in ("os_system", "terminal"))
