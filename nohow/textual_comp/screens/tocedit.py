from __future__ import annotations

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

    Screen layout:
    - BookEditWidget (reactive title + Input)
    - TextArea for markdown content
    - Bottom horizontal bar with OK / Cancel buttons

    When OK is pressed the screen sets self.result = {"title": ..., "content": ...}
    and requests to be popped; when Cancel is pressed self.result is set to None.
    """

    DEFAULT_CSS = """
    TOCEditScreen {

    }
    """

    BINDINGS: list[tuple[str, str, str]] = []

    content: reactive[str] = reactive("")

    def __init__(self, initial_title: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self.initial_title = initial_title
        self.result = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield BookEditWidget(id="book_edit", book_title=self.initial_title)
        yield Footer()

    def on_mount(self) -> None:
        # Not database-related; leaving as-is.
        try:
            self.query_one("#markdown_area", TextArea).focus()
        except Exception:
            pass

    def on_button_pressed(self, event) -> None:
        """Handle OK / Cancel button presses.

        OK: collect the title and markdown content into self.result and pop the screen.
        Cancel: set self.result = None and pop the screen.
        """
        button_id = getattr(event.button, "id", None) or getattr(
            event.button, "label", None
        )

        if button_id == "ok":
            try:
                book_widget = self.query_one("#book_edit", BookEditWidget)
                title = book_widget.book_title
            except Exception:
                title = ""

            try:
                content = getattr(self.query_one("#markdown_area", TextArea), "value", "")
            except Exception:
                content = ""

            saved = False
            error: str | None = None
            session = None

            try:
                engine = setup_database()
                session = get_session(engine)

                existing = None
                if title:
                    # Prefer the canonical column name.
                    try:
                        existing = session.query(Book).filter_by(title=title).first()
                    except Exception as e:
                        # Fallback: try alternative column names, but do not silence failures.
                        self.app.log(
                            f"DB query using filter_by(title=...) failed; trying fallbacks. Error: {e!r}"
                        )
                        for col in ("title", "name"):
                            if not hasattr(Book, col):
                                continue
                            try:
                                existing = (
                                    session.query(Book)
                                    .filter(getattr(Book, col) == title)
                                    .first()
                                )
                                if existing:
                                    break
                            except Exception as e2:
                                self.app.log(
                                    f"DB query fallback using column '{col}' failed. Error: {e2!r}"
                                )

                if existing is not None:
                    # Update existing record with best-effort field names.
                    updated_any = False

                    for col in ("title", "name"):
                        if hasattr(existing, col):
                            setattr(existing, col, title)
                            updated_any = True
                            break

                    for col in ("toc", "content", "markdown", "body"):
                        if hasattr(existing, col):
                            setattr(existing, col, content)
                            updated_any = True
                            break

                    if not updated_any:
                        raise RuntimeError(
                            "Book model has no recognized fields to update (expected title/name and toc/content/markdown/body)."
                        )

                    session.add(existing)
                else:
                    # Create new Book instance using common field names (best-effort).
                    kwargs: dict[str, str] = {}

                    title_field = next(
                        (col for col in ("title", "name") if hasattr(Book, col)), None
                    )
                    content_field = next(
                        (col for col in ("toc", "content", "markdown", "body") if hasattr(Book, col)),
                        None,
                    )

                    if title_field is None or content_field is None:
                        raise RuntimeError(
                            "Book model has no recognized fields (expected title/name and toc/content/markdown/body)."
                        )

                    kwargs[title_field] = title
                    kwargs[content_field] = content

                    new = Book(**kwargs)
                    session.add(new)

                session.commit()
                saved = True

            except Exception as e:
                error = str(e)
                self.app.log(f"Failed to save book/TOC to database: {e!r}")
                if session is not None:
                    try:
                        session.rollback()
                    except Exception as rb_e:
                        self.app.log(f"Database rollback failed: {rb_e!r}")
            finally:
                if session is not None:
                    try:
                        session.close()
                    except Exception as close_e:
                        self.app.log(f"Database session close failed: {close_e!r}")

            self.result = {"title": title, "content": content, "saved": saved, "error": error}

            try:
                self.app.pop_screen()
            except Exception:
                pass

        elif button_id == "cancel":
            self.result = None
            try:
                self.app.pop_screen()
            except Exception:
                pass
