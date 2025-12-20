from __future__ import annotations

from textual.app import App

from nohow.textual_comp.screens.booklist import BookListScreen


class NohowApp(App):
    """Main Textual application."""

    TITLE = "Nohow"

    def on_mount(self) -> None:
        self.push_screen(BookListScreen())


def main() -> None:
    NohowApp().run()


if __name__ == "__main__":
    main()
