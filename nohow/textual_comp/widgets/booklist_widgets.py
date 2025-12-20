from __future__ import annotations

from textual.containers import VerticalScroll, Grid
import math
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Static


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
        try:
            title = self.query_one("#title", Static)
        except NoMatches:
            return
        title.update(new_value)


class AddBookElement(Widget):
    """A fixed-size widget (same shape as BookElement) containing an Add button."""

    DEFAULT_CSS = """
    AddBookElement {
        width: 30;
        height: 9;
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

    /* A scrollable grid: fixed to 3 columns, rows as needed.
       The view contains a VerticalScroll with an inner Grid.
       We control row count in Python to ensure a minimum of 2 rows. */
    BooksView > VerticalScroll {
        width: 100%;
        height: 100%;
        padding: 1;
    }

    BooksView > VerticalScroll > Grid {
        /* Use basic grid settings without a fixed column template so the
           Python layout logic (mounting items into the Grid) determines
           how many items appear per row. Keep rows flexible in height. */
        display: grid;
        grid-auto-flow: row;
        grid-auto-rows: minmax(5, auto);
        gap: 1 1;
        width: 100%;
    }
    """

    def compose(self):
        yield VerticalScroll(
            Grid(id="books_grid"),
            id="books_scroll",
        )

    async def set_books(self, books) -> None:
        """Receive the current list of books from the DB and populate the grid.

        Layout rules:
        - Fixed columns = 3
        - Minimum rows = 2
        - Fill remaining cells with AddBookElement instances so the grid is always full.
        """
        scroll = self.query_one("#books_scroll", VerticalScroll)
        grid = self.query_one("#books_grid", Grid)
        await grid.remove_children()

        # Normalize incoming books into a list of titles.
        titles: list[str] = []
        for book in books or []:
            titles.append(getattr(book, "title", None) or getattr(book, "name", None) or str(book))

        columns = 3
        rows = max(2, (len(titles) + columns - 1) // columns)
        total_cells = rows * columns

        # Mount book elements in order (left-to-right, top-to-bottom).
        for title in titles:
            grid.mount(BookElement(book_title=title))

        # Fill remaining cells with AddBookElement instances (no duplicate ids).
        for _ in range(total_cells - len(titles)):
            grid.mount(AddBookElement())

    async def add_book(self, book_title: str) -> None:
        """Insert a new book at the start of the list by rebuilding the grid.

        We collect existing book titles and rebuild the grid so the layout rules
        (3 columns, at least 2 rows) are preserved. This keeps logic simple and
        consistent across different numbers of books.
        """
        grid = self.query_one("#books_grid", Grid)

        # Collect existing book titles in order.
        existing_titles = [
            getattr(child, "book_title", None)
            for child in grid.children
            if isinstance(child, BookElement)
        ]

        # New book becomes first.
        titles = [book_title] + existing_titles

        await self.set_books(titles)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the Add button click from inside this widget."""
        if event.button.id != "add_book_button":
            return

        # Spawn a worker to create the book in the DB, then update the UI.
        self.run_worker(self._create_book_and_insert(), exclusive=True)

    async def _create_book_and_insert(self) -> None:
        """Create a new book in the database and insert it into the list."""
        default_title = "New Book"

        created_book = None
        try:
            from nohow.db.models import Book
            from nohow.db.utils import get_session, setup_database

            engine = setup_database()
            session = get_session(engine)

            try:
                created_book = Book(title=default_title)
                session.add(created_book)
                session.commit()
                try:
                    session.refresh(created_book)
                except Exception:
                    pass
            finally:
                try:
                    session.close()
                except Exception:
                    pass

        except Exception:
            created_book = None

        # Update UI (we at least insert the title we attempted to create).
        title = (
            getattr(created_book, "title", None)
            or getattr(created_book, "name", None)
            or default_title
        )
        await self.add_book(title)

        # Prepare to jump to another screen later.
        # self.emit("action change screen somethin...")
