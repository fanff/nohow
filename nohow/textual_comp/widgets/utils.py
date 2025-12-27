
from textual.widget import Widget
from textual.widgets import Button, OptionList, Static, LoadingIndicator, Label
from textual.widgets.option_list import Option
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.binding import Binding
from textual.app import ComposeResult


class IsTyping(Horizontal):
    DEFAULT_CSS = """
    IsTyping {
        height: 1;
        }
    """

    def compose(self) -> ComposeResult:
        yield LoadingIndicator()
        yield Label("  AI is responding ")
