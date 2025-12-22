from __future__ import annotations

from textual.containers import VerticalScroll, Grid
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Static, Input
from nohow.db.models import Book
from nohow.db.utils import get_session, setup_database


class BookElement(Widget):
    """A fixed-size widget representing a single book entry."""

    DEFAULT_CSS = """
    BookElement {
        width: 100%;
        height: 100%;
        border: solid $primary;
        padding: 1 1;
        margin: 1 1;
    }

    BookElement:hover {
        background: $accent;
    }
    """

    class ChatOnBook(Message):
        """Message emitted when this BookElement is clicked to request chatting."""

        def __init__(
            self, sender: "BookElement", book_title: str, book_id: int | None
        ) -> None:
            # Ensure the message bubbles up so parent containers/screens can catch it.
            super().__init__()
            self.book_title = book_title
            self.book_id = book_id

    class EditBook(Message):
        """Message emitted when this BookElement is clicked to request editing."""

        def __init__(
            self, sender: "BookElement", book_title: str, book_id: int | None
        ) -> None:
            # Ensure the message bubbles up so parent containers/screens can catch it.
            super().__init__()
            self.book_title = book_title
            self.book_id = book_id

    book_title: reactive[str] = reactive("")

    def __init__(
        self, book_title: str = "", book_id: int | None = None, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.book_title = book_title
        self.book_id = book_id

    def compose(self):
        yield Static(self.book_title, id="title")

    def watch_book_title(self, new_value: str) -> None:
        try:
            title = self.query_one("#title", Static)
        except NoMatches:
            title = None
        else:
            title.update(new_value)

    from textual.events import Click

    def on_click(self, event: Click) -> None:
        """Handle clicks on this widget and emit an EditBook message."""
        event.stop()  # Stop further propagation.

        if event.button == 1:  # Left click only
            self.post_message(self.ChatOnBook(self, self.book_title, self.book_id))

        else:
            # Post a message that bubbles up to parent widgets / app.
            self.post_message(self.EditBook(self, self.book_title, self.book_id))


class AddBookElement(Widget):
    """A fixed-size widget (same shape as BookElement) containing an Add button."""

    DEFAULT_CSS = """
    AddBookElement {
        width: 100%;
        height: 100%;
        
        padding: 1 1;
        margin: 1 1;
        content-align: center middle;
    }

    AddBookElement Button {
        width: 70%;
    }
    """

    def compose(self):
        yield Button("Add", id="add_book_button", variant="primary")


class BooksView(Widget, can_focus=False):
    """Unfocusable container holding a scrollable vertical list of books."""

    DEFAULT_CSS = """
    BooksView {
        width: 100%;
        height: 100%;
        
    }

    BooksView > VerticalScroll {
        width: 100%;
        height: 100%;
        padding: 1;
    }

    BooksView > VerticalScroll > Grid {
        border: solid $accent;
        grid-size: 3 3;
        
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
        grid limited to 3 columns and 3 rows (9 total).
        - Fill remaining cells with AddBookElement instances so the grid is always full.
        """
        # scroll = self.query_one("#books_scroll", VerticalScroll)
        grid = self.query_one("#books_grid", Grid)
        await grid.remove_children()

        # Normalize incoming books into (id, title) pairs.
        items: list[tuple[int | None, str]] = []
        for book in books or []:
            if isinstance(book, str):
                items.append((None, book))
                continue

            book_id = getattr(book, "id", None)
            title = (
                getattr(book, "title", None) or getattr(book, "name", None) or str(book)
            )
            items.append((book_id, title))

        columns = 3
        rows = 3
        total_cells = rows * columns

        # Mount book elements in order (left-to-right, top-to-bottom).
        for book_id, title in items[:total_cells]:
            await grid.mount(BookElement(book_title=title, book_id=book_id))

        # Fill remaining cells with AddBookElement instances (no duplicate ids).
        for _ in range(total_cells - len(items)):
            await grid.mount(AddBookElement())

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

        engine = setup_database()
        with get_session(engine) as session:

            created_book = Book(title=default_title, toc="")
            session.add(created_book)
            session.commit()
            session.refresh(created_book)

        # Update UI (we at least insert the title we attempted to create).
        title = created_book.title
        await self.add_book(title)

        # Prepare to jump to another screen later.
        # self.emit("action change screen somethin...")

    def on_book_element_edit_book(self, message: BookElement.EditBook) -> None:
        """Handle EditBook messages from BookElement and push an edit screen."""
        # Import locally to avoid top-level import cycles.
        from nohow.textual_comp.screens.tocedit import TOCEditScreen

        self.app.push_screen(
            TOCEditScreen(book_id=message.book_id, initial_title=message.book_title)
        )

    async def on_book_element_chat_on_book(
        self, message: BookElement.ChatOnBook
    ) -> None:
        """Handle ChatOnBook messages from BookElement and push a chat screen."""
        # Import locally to avoid top-level import cycles.
        # await self.app.pop_screen()
        from nohow.textual_comp.screens.tocreader import TOCReaderScreen

        await self.app.push_screen(TOCReaderScreen(message.book_id))
