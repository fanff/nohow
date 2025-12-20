from textual.screen import Screen


class BookListScreen(Screen):
    """Écran liste des livres (placeholder)."""

    BINDINGS: list[tuple[str, str, str]] = []

    def compose(self):
        """Compose les composants UI (vide pour l’instant)."""
        return
