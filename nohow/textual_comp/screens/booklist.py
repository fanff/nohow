from textual.screen import Screen


class BookListScreen(Screen):
    """Écran liste des livres (placeholder)."""

    BINDINGS = [
        ("j", "focus_next", "Focus suivant"),
        ("k", "focus_previous", "Focus précédent"),
    ]

    def compose(self):
        """Compose les composants UI (vide pour l’instant)."""
        return
