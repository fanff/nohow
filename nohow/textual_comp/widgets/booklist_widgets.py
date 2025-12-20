from __future__ import annotations

from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Static
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


class AddBookElement(Widget):
    """A fixed-size widget (same shape as BookElement) containing an Add button."""

    DEFAULT_CSS = """
    AddBookElement {
        width: 20;
        height: 5;
        border: solid $primary;
        padding: 1 1;
        margin: 1 1;
        content-align: center middle;
    }

    AddBookElement Button {
        width: 100%;
    }
    """

    def compose(self):
        yield Button("Add", id="add_book_button", variant="primary")


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
        yield VerticalScroll(
            AddBookElement(id="add_book_element"),
            id="books_scroll",
        )

    def set_books(self, books) -> None:
        """Receive the current list of books from the DB and populate the view."""
        scroll = self.query_one("#books_scroll", VerticalScroll)
        scroll.remove_children()

        # Always keep the "Add" element at the top.
        scroll.mount(AddBookElement(id="add_book_element"))

        for book in books or []:
            title = getattr(book, "title", None) or getattr(book, "name", None) or str(book)
            scroll.mount(BookElement(book_title=title))

    def add_book(self, book_title: str) -> None:
        """Insert a new book at the start of the list, after the Add widget."""
        scroll = self.query_one("#books_scroll", VerticalScroll)
        children = list(scroll.children)

        # Ensure the Add widget exists and is first.
        if not children or not isinstance(children[0], AddBookElement):
            scroll.mount(AddBookElement(id="add_book_element"), before=0)
            children = list(scroll.children)

        insert_index = 1  # right after the Add widget
        scroll.mount(BookElement(book_title=book_title), before=insert_index)
