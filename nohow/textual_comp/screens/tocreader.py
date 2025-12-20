from textual.screen import Screen


class TOCReaderScreen(Screen):
    """Écran de lecture / conversation sur un chapitre (placeholder)."""

    BINDINGS: list[tuple[str, str, str]] = []

    def compose(self):
        """Compose les composants UI (vide pour l’instant)."""
        return
