from __future__ import annotations

from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import VerticalScroll


class BookElement(Widget):
    """A fixed-size widget representing a single book entry."""

    DEFAULT_CSS = """
    BookElement {
        width: 20;
        height: 5;
        border: solid $primary;
        padding: 1 1;
        margin: 1 1;
    }
    """

    book_title: reactive[str] = reactive("")

    def __init__(self, book_title: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self.book_title = book_title

    def compose(self):
        yield Static(self.book_title, id="title")

    def watch_book_title(self, new_value: str) -> None:
        title = self.query_one("#title", Static)
        title.update(new_value)


class BooksView(Widget):
    """Unfocusable container holding a scrollable vertical list of books."""

    can_focus = False

    DEFAULT_CSS = """
    BooksView {
        width: 100%;
        height: 100%;
    }

    BooksView > VerticalScroll {
        width: 100%;
        height: 100%;
    }
    """

    def compose(self):
        yield VerticalScroll(id="books_scroll")

    def set_books(self, books) -> None:
        """Receive the current list of books from the DB (placeholder for now)."""
        return
