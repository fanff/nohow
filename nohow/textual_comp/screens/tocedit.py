from __future__ import annotations
import json
from nohow.mkdutils import extract_toc_tree

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Input, Static, TextArea

from nohow.db.models import Book
from nohow.db.utils import get_session, setup_database


class BookEditWidget(Widget):
    """Widget exposing a reactive book_title and an Input bound to it.

    This small widget keeps a reactive 'book_title' attribute in sync with
    an Input widget so parent screens can read the current title at any time.
    """

    DEFAULT_CSS = """
    BookEditWidget {
        border: solid $secondary;
        padding: 1 1;
        height: auto;
    }
    BookEditWidget > Horizontal#buttons {
        height: 4;
        align-vertical: bottom;
        padding-top: 1;
    }
    BookEditWidget > Input#title_input {
        height: 3;
        }
    BookEditWidget > TextArea {
        height: 1fr;
    }
    """

    book_title: reactive[str] = reactive("")

    def __init__(self, book_title: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self.book_title = book_title

    def compose(self) -> ComposeResult:
        yield Static("Title:", id="title_label")
        yield Input(
            value=self.book_title,
            placeholder="Enter book title...",
            id="title_input",
        )
        yield TextArea(tooltip="Write markdown here...", id="markdown_area")
        yield Horizontal(
            Button("OK", id="ok", variant="primary"),
            Button("Cancel", id="cancel", variant="error"),
            id="buttons",
        )

    def on_mount(self) -> None:
        # Not database-related; leaving as-is.
        try:
            self.query_one("#title_input", Input).focus()
        except Exception:
            pass

    def on_input_changed(self, event) -> None:
        # Not database-related; leaving as-is.
        try:
            self.book_title = event.value
        except Exception:
            pass


class TOCEditScreen(Screen):
    """Écran d’édition de la table des matières.

    When OK is pressed:
    - load Book by id
    - replace title and toc
    - commit
    - expose result and pop screen

    When Cancel is pressed:
    - set result to None and pop screen
    """

    DEFAULT_CSS = """
    TOCEditScreen {

    }
    """

    BINDINGS: list[tuple[str, str, str]] = []

    content: reactive[str] = reactive("")

    def __init__(self, book_id: int, initial_title: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self.book_id = book_id
        self.initial_title = initial_title
        self.result = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield BookEditWidget(id="book_edit", book_title=self.initial_title)
        yield Footer()

    def on_mount(self) -> None:

        book_widget = self.query_one("#book_edit", BookEditWidget)
        toc = self.query_one("#markdown_area", TextArea)
        engine = setup_database()
        with get_session(engine) as session:
            book = session.query(Book).filter_by(id=self.book_id).one()
            toc.text = book.toc or ""
            book_widget.book_title = book.title or ""
        toc.focus()

    def on_button_pressed(self, event) -> None:
        button_id = getattr(event.button, "id", None) or getattr(
            event.button, "label", None
        )

        if button_id == "ok":
            book_widget = self.query_one("#book_edit", BookEditWidget)
            toc = self.query_one("#markdown_area", TextArea)

            title = book_widget.book_title
            toc_text = toc.text
            toc_tree = extract_toc_tree(toc_text)
            engine = setup_database()
            session = get_session(engine)
            try:
                book = session.query(Book).filter_by(id=self.book_id).one()
                book.title = title
                book.toc = toc_text
                book.toc_tree = json.dumps(toc_tree.to_json())
                session.add(book)
                session.commit()
            finally:
                session.close()

            self.result = {"book_id": self.book_id, "title": title, "toc": toc_text}
            self.app.pop_screen()

        elif button_id == "cancel":
            self.result = None
            self.app.pop_screen()
