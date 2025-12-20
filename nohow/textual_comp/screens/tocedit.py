from textual.screen import Screen
from textual.reactive import reactive
from textual.widget import Widget
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from textual.widgets import Static, Input, Button, TextArea

class BookEditWidget(Widget):
    """Widget exposing a reactive book_title and an Input bound to it.

    This small widget keeps a reactive 'book_title' attribute in sync with
    an Input widget so parent screens can read the current title at any time.
    """

    book_title: reactive[str] = reactive("")

    def __init__(self, book_title: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        # Initialize the reactive with the provided initial value.
        self.book_title = book_title

    def compose(self) -> ComposeResult:
        yield Static("Title:", id="title_label")
        yield Input(value=self.book_title, placeholder="Enter book title...", id="title_input")

    def on_mount(self) -> None:
        # Focus the title input when the widget mounts if possible.
        try:
            self.query_one("#title_input", Input).focus()
        except Exception:
            pass

    def on_input_changed(self, event) -> None:
        # Keep the reactive value in sync with the Input's value.
        try:
            self.book_title = event.value
        except Exception:
            # Be defensive: ignore unexpected event shapes.
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

    BINDINGS: list[tuple[str, str, str]] = []

    content: reactive[str] = reactive("")

    def __init__(self, initial_title: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        # Title to pre-populate the editor with.
        self.initial_title = initial_title
        # Result will be set to a dict {"title":..., "content":...} on OK, or None on cancel.
        self.result = None

    def compose(self) -> ComposeResult:
        yield Vertical(
            BookEditWidget(id="book_edit", book_title=self.initial_title),
            TextArea(placeholder="Write markdown here...", id="markdown_area"),
            Horizontal(
                Button("OK", id="ok", variant="primary"),
                Button("Cancel", id="cancel", variant="error"),
                id="buttons",
            ),
            id="main",
        )

    def on_mount(self) -> None:
        # Focus the markdown area so users can start typing immediately.
        try:
            self.query_one("#markdown_area", TextArea).focus()
        except Exception:
            pass

    def on_button_pressed(self, event) -> None:
        """Handle OK / Cancel button presses.

        OK: collect the title and markdown content into self.result and pop the screen.
        Cancel: set self.result = None and pop the screen.
        """
        button_id = getattr(event.button, "id", None) or getattr(event.button, "label", None)
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
            # Expose results so the caller can inspect them after the screen is popped.
            self.result = {"title": title, "content": content}
            try:
                # Prefer app.pop_screen() to remove the top-most pushed screen.
                self.app.pop_screen()
            except Exception:
                pass
        elif button_id == "cancel":
            self.result = None
            try:
                self.app.pop_screen()
            except Exception:
                pass
