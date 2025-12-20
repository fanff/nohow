from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header

from nohow.textual_comp.widgets.booklist_widgets import BooksView


class BookListScreen(Screen):
    """Screen listing books."""

    BINDINGS = [
        ("j", "focus_next", "Focus next"),
        ("k", "focus_previous", "Focus previous"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the UI components."""
        yield Header()
        yield BooksView(id="books_view")
        yield Footer()

    def on_mount(self) -> None:
        """Load books from the database and pass them to the BooksView."""
        self.run_worker(self._load_books(), exclusive=True)

    async def _load_books(self) -> None:
        books = []

        try:
            from nohow.db.utils import get_session, setup_database
            from nohow.db.models import Book

            engine = setup_database()
            session = get_session(engine)

            try:
                result = session.query(Book).all()
                books = result or []
            finally:
                try:
                    session.close()
                except Exception:
                    pass

        except Exception:
            books = []

        books_view = self.query_one("#books_view", BooksView)
        books_view.set_books(books)
