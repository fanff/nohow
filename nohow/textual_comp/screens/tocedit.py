from textual.screen import Screen


class TOCEditScreen(Screen):
    """Écran d’édition de la table des matières (placeholder)."""

    BINDINGS: list[tuple[str, str, str]] = []

    def compose(self):
        """Compose les composants UI (vide pour l’instant)."""
        return
