from __future__ import annotations
import yaml
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from nohow.prompts.utils import (
    new_message_of_type,
)  # noqua, this force slow import early
from typing import Optional

from textual.app import App

from nohow.textual_comp.screens.booklist import BookListScreen

DEFAULT_CONFIG = {
    "model_name": "gpt-3.5-turbo",
    "aiprovider_key": "",
}


class AppContext:
    """Context object to hold global application state."""

    def __init__(self) -> None:
        self.model_name: str | None = None
        self.aiprovider_key: str | None = None
        self.llm: ChatOpenAI | None = None

    @classmethod
    def from_yaml(cls, path: Path) -> "AppContext":
        """Load application context from a yaml file."""
        # Placeholder implementation; replace with actual file loading logic
        config = DEFAULT_CONFIG.copy()
        with open(str(path), "r", encoding="utf-8") as f:
            # load values from yaml
            user_config = yaml.safe_load(f) or {}
            for k, v in config.items():
                if k in user_config:
                    config[k] = user_config[k]
        c = cls()
        for key, value in config.items():
            setattr(c, key, value)
        c.llm = ChatOpenAI(
            model=c.model_name, temperature=0.7, api_key=c.aiprovider_key
        )  # uses env var OPENAI_API_KEY
        return c


class NohowApp(App):
    """Main Textual application."""

    TITLE = "Nohow"

    def __init__(self, context: Optional[AppContext] = None) -> None:
        super().__init__()

        self.app_context = context or AppContext.from_yaml(Path(".nohow.yml"))

    def on_mount(self) -> None:
        self.push_screen(BookListScreen())


def main() -> None:
    NohowApp().run()


if __name__ == "__main__":
    main()
