from __future__ import annotations
from typing import List

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, Rule
from nohow.db.utils import get_session, setup_database
from nohow.db.models import Book
from nohow.textual_comp.widgets.booklist_widgets import BooksView


class BookListScreen(Screen):
    """Screen listing books."""

    BINDINGS = [
        ("j", "focus_next", "Focus next"),
        ("k", "focus_previous", "Focus previous"),
    ]
    DEFAULT_CSS = """
    BookListScreen {
        align: center top;
    }
    
    #books_view {
        margin-top: 3;
        height: 1fr;
        width: 70%;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the UI components."""
        yield Header()
        yield BooksView(id="books_view")
        yield Footer()

    def on_mount(self) -> None:
        """Load books from the database and pass them to the BooksView."""
        self.run_worker(self._load_books(), exclusive=True)

    def _on_screen_resume(self):
        super()._on_screen_resume()
        """Reload books when the screen gains focus."""
        self.run_worker(self._load_books(), exclusive=True)

    async def _load_books(self) -> None:
        books = []

        engine = self.app.get_db()
        with get_session(engine) as session:
            books: List[Book] = session.query(Book).all()

        books_view = self.query_one("#books_view", BooksView)

        await books_view.set_books(books)
