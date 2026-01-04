from __future__ import annotations
from pathlib import Path
from textual.containers import Horizontal

from textual import on
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Footer, Header, Label, Input, Button, Static, MaskedInput


class ConfigScreen(Screen):
    """Screen listing books."""

    BINDINGS = [
        ("j", "focus_next", "Focus next"),
        ("k", "focus_previous", "Focus previous"),
    ]
    DEFAULT_CSS = """
    ConfigScreen {
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
        yield Static("Configuration Screen - Under Construction", id="config_message")

        yield ConfigForm()
        with Horizontal(id="config_buttons"):
            yield Button("Back", id="back_button")
            yield Button("Save", id="save_button")
        yield Footer()

    @on(Button.Pressed, "#back_button")
    def on_back_button_pressed(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#save_button")
    def on_save_button_pressed(self) -> None:
        from nohow.main import AppContext

        app_context: AppContext = self.app.app_context
        model_name_input = self.query_one("#model_name_input", Input)
        aiprovider_key_input = self.query_one("#aiprovider_key_input", Input)

        app_context.model_name = model_name_input.value
        app_context.aiprovider_key = aiprovider_key_input.value
        app_context.to_yaml(Path(self.app.yaml_config_path))
        # Here you would typically save the configuration to a file
        self.app.pop_screen()


class ConfigForm(Static):
    """Configuration form widget."""

    DEFAULT_CSS = """
    ConfigForm {
        align: center middle;
        width: 60%;
        height: auto;
        border: round $accent;
        padding: 2;
        background: $panel;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the UI components."""

        yield Label(f"Config Path:")
        yield Label(f"{self.app.yaml_config_path}")
        yield Label(f"Database Path:")
        yield Label(f"{self.app.db_path}")

        yield Label("Model Name:")
        yield Input(placeholder="Enter model name", id="model_name_input")
        yield Label("AI Provider Key:")
        yield Input(
            placeholder="Enter AI provider key",
            id="aiprovider_key_input",
            password=True,
        )

    def _on_mount(self, event):
        super()._on_mount(event)
        from nohow.main import AppContext

        app_context: AppContext = self.app.app_context
        model_name_input = self.query_one("#model_name_input", Input)
        aiprovider_key_input = self.query_one("#aiprovider_key_input", Input)

        model_name_input.value = app_context.model_name or ""
        aiprovider_key_input.value = app_context.aiprovider_key or ""
