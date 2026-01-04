from __future__ import annotations
from sqlalchemy import create_engine
import yaml
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from nohow.db.utils import setup_database
from nohow.prompts.utils import (
    new_message_of_type,
)  # noqua, this force slow import early
from typing import Optional

from platformdirs import user_data_dir
from pathlib import Path
from textual.app import App
from nohow.textual_comp.screens.config import ConfigScreen
from nohow.textual_comp.screens.tocedit import TOCEditScreen
from nohow.textual_comp.screens.tocreader import TOCReaderScreen
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

    def to_yaml(self, path: Path) -> None:
        """Save application context to a yaml file."""
        config = {
            "model_name": self.model_name,
            "aiprovider_key": self.aiprovider_key,
        }
        with open(str(path), "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)

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

    BINDINGS = [
        ("ctrl+o", "show_config", "Config"),
        ("j", "app.focus_next", "Focus Next"),
        ("k", "app.focus_previous", "Focus Previous"),
    ]

    TITLE = "Nohow"

    def __init__(self, cfg_dir: Path, context: Optional[AppContext] = None) -> None:

        yaml_config = cfg_dir / ".nohow.yml"
        if not yaml_config.exists():
            # create default config file
            with open(str(yaml_config), "w", encoding="utf-8") as f:
                yaml.safe_dump(DEFAULT_CONFIG, f)

        self.db_path = cfg_dir / "nohow.db"
        if not self.db_path.exists():
            # create empty db file
            setup_database(db_url=f"sqlite:///{self.db_path}")

        self.app_context = context or AppContext.from_yaml(yaml_config)
        self.yaml_config_path = yaml_config
        self.db_path = self.db_path
        super().__init__()

    def get_db(self):
        db_url = f"sqlite:///{self.db_path}"  # str(self.db_path)
        engine = create_engine(db_url)
        return engine

    def on_mount(self) -> None:
        self.push_screen(BookListScreen())

    def action_show_config(self) -> None:
        """Show the configuration screen."""
        self.push_screen(ConfigScreen())


def get_nohow_dir() -> Path:

    # returns e.g. ~/.local/share/NoHow or C:\Users\You\AppData\Local\NoHow
    p = Path(user_data_dir("nohow"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config-dir",
        help="Path to NoHow config directory",
        required=False,
        default="",
    )
    args = parser.parse_args()

    if args.config_dir == "":
        cfg_dir = get_nohow_dir()
    else:
        cfg_dir = Path(args.config_dir)

    NohowApp(cfg_dir=cfg_dir).run()


if __name__ == "__main__":
    main()
