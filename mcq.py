from nohow.prompts.mcq import MCQGen, MCQForm
from textual.widget import Widget
from textual.app import ComposeResult, App
from textual.widgets import Header, Footer, Label, Checkbox, Markdown


class MCQFormWidget(Widget):
    """Widget for displaying MCQ forms."""

    DEFAULT_CSS = """
    MCQFormWidget {
        border: solid $secondary;
        padding: 1 1;
        height: auto;
    }
    """

    BINDINGS = []

    _mcq: MCQGen | None = None

    def compose(self) -> ComposeResult:
        yield Markdown("MCQ Form - Under Construction", id="mcq_form_label")
        yield Checkbox("Option 1", id="option_1")
        yield Checkbox("Option 2", id="option_2")
        yield Checkbox("Option 3", id="option_3")
        yield Checkbox("Option 4", id="option_4")

    def set_mcq(self, mcq: MCQGen) -> None:
        """Set the MCQ to display."""
        self._mcq = mcq
        # updsate the question
        mcq_label = self.query_one("#mcq_form_label", Markdown)
        mcq_label.update(mcq.question)
        # update the options
        updated_options = []
        for idx, option in enumerate(mcq.choices):
            checkbox = self.query_one(f"#option_{idx+1}", Checkbox)
            checkbox.label = option
            updated_options.append(checkbox)
        # hide unused options
        for idx in range(len(mcq.choices), 4):
            checkbox = self.query_one(f"#option_{idx+1}", Checkbox)
            checkbox.display = False

    def on_mount(self) -> None:
        if self._mcq:
            self.set_mcq(self._mcq)


class MCQDemo(App):
    """Main Textual application."""

    BINDINGS = [
        ("j", "app.focus_next", "Focus Next"),
        ("k", "app.focus_previous", "Focus Previous"),
    ]

    TITLE = "MCQDemo"

    def compose(self):
        yield Header()
        with open("mcq_form.json", "r", encoding="utf-8") as f:
            json_data = f.read()
        mcq_form = MCQForm.model_validate_json(json_data)
        for mcq in mcq_form.items:
            mcq_widget = MCQFormWidget()
            mcq_widget._mcq = mcq
            yield mcq_widget
        yield Footer()


if __name__ == "__main__":
    MCQDemo().run()
