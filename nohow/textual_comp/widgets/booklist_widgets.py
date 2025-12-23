from __future__ import annotations
from textual import on
from regex import W
from typing import List

from textual.containers import VerticalScroll, Grid
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Static, Input, ListView, ListItem
from nohow.db.models import Book
from nohow.db.utils import get_session, setup_database
from textual.events import Click, DescendantFocus, DescendantBlur


class BookElement(Widget, can_focus_children=True):
    """A fixed-size widget representing a single book entry."""

    DEFAULT_CSS = """
    BookElement {
        width: 100%;
        height: auto;
        border-left: solid $primary;
        padding: 1 1;
        margin: 1 1;

        &.-focused {
            border-left: thick $primary;
            background: $boost;
        }
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
            self.sender = sender

    class EditBook(Message):
        """Message emitted when this BookElement is clicked to request editing."""

        def __init__(
            self, sender: "BookElement", book_title: str, book_id: int | None
        ) -> None:
            # Ensure the message bubbles up so parent containers/screens can catch it.
            super().__init__()
            self.book_title = book_title
            self.book_id = book_id
            self.sender = sender

    book_title: reactive[str] = reactive("")

    def __init__(
        self, book_title: str = "", book_id: int | None = None, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.book_title = book_title
        self.book_id = book_id

    def compose(self):
        yield Static(self.book_title, id="title")
        yield Button("Edit", id="edit_button", variant="primary")
        yield Button("Chat", id="chat_button", variant="success")

    def watch_book_title(self, new_value: str) -> None:
        try:
            title = self.query_one("#title", Static)
        except NoMatches:
            title = None
        else:
            title.update(new_value)

    @on(DescendantFocus)
    def on_descendant_focus(self, event: DescendantFocus) -> None:
        """Handle focus events from child widgets to highlight this element."""
        self.add_class("-focused")

    @on(DescendantBlur)
    def on_descendant_blur(self, event: DescendantBlur) -> None:
        """Handle blur events from child widgets to remove highlight."""
        self.remove_class("-focused")

    @on(Button.Pressed, "#chat_button")
    def on_chat_click(self, event: Button.Pressed) -> None:
        """Handle clicks on this widget and emit an EditBook message."""
        event.stop()  # Stop further propagation.

        self.post_message(self.ChatOnBook(self, self.book_title, self.book_id))

    @on(Button.Pressed, "#edit_button")
    def on_edit_click(self, event: Button.Pressed) -> None:
        event.stop()
        self.post_message(self.EditBook(self, self.book_title, self.book_id))

    def update_book_content(self, book_title: str) -> None:
        """Update the book title displayed in this widget."""
        self.book_title = book_title


class AddBookElement(Widget):
    """A fixed-size widget (same shape as BookElement) containing an Add button."""

    DEFAULT_CSS = """
    AddBookElement {
        height: auto;
        
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

    #book_list_view {
        height: 1fr;
        width: 100%;
    }

    #add_book_element {
        height: 5;
        width: 100%;
    }
    
    """

    def compose(self):

        yield VerticalScroll(id="book_list_view")
        yield AddBookElement(id="add_book_element")

    async def set_books(self, books: List[Book]) -> None:
        """Receive the current list of books from the DB and populate the List."""
        # scroll = self.query_one("#books_scroll", VerticalScroll)
        grid = self.query_one("#book_list_view", VerticalScroll)
        await grid.remove_children("*")

        # Normalize incoming books into (id, title) pairs.
        items: list[tuple[int | None, str]] = []
        for book in books:

            book_id = int(book.id)
            title = str(book.title)

            await grid.mount(BookElement(book_title=title, book_id=book_id))

    async def add_book(self, book: Book) -> BookElement:
        """Insert a new book at the start of the list by rebuilding the grid.

        We collect existing book titles and rebuild the grid so the layout rules
        (3 columns, at least 2 rows) are preserved. This keeps logic simple and
        consistent across different numbers of books.
        """
        grid = self.query_one("#book_list_view", VerticalScroll)
        be = BookElement(book_title=book.title, book_id=book.id)
        await grid.mount(be)
        return be

    @on(Button.Pressed, "#add_book_button")
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the Add button click from inside this widget."""

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
        be = await self.add_book(created_book)

        # Prepare to jump to another screen later.
        # self.emit("action change screen somethin...")
        from nohow.textual_comp.screens.tocedit import TOCEditScreen

        self.app.push_screen(
            TOCEditScreen(
                book_id=created_book.id,
                screen_caller=be,
                initial_title=created_book.title,
            )
        )

    def on_book_element_edit_book(self, message: BookElement.EditBook) -> None:
        """Handle EditBook messages from BookElement and push an edit screen."""
        # Import locally to avoid top-level import cycles.
        from nohow.textual_comp.screens.tocedit import TOCEditScreen

        self.app.push_screen(
            TOCEditScreen(
                book_id=message.book_id,
                screen_caller=message.sender,
                initial_title=message.book_title,
            )
        )

    async def on_book_element_chat_on_book(
        self, message: BookElement.ChatOnBook
    ) -> None:
        """Handle ChatOnBook messages from BookElement and push a chat screen."""
        # Import locally to avoid top-level import cycles.
        # await self.app.pop_screen()
        from nohow.textual_comp.screens.tocreader import TOCReaderScreen

        await self.app.push_screen(TOCReaderScreen(message.book_id))
