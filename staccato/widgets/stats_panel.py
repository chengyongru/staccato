"""Universal statistics display panel for Staccato v3.0."""

from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Label


class MostRecentPairDisplay(Vertical):
    """Display for the most recent key pair overlap."""

    DEFAULT_CSS = """
    MostRecentPairDisplay {
        width: 1fr;
        content-align: center middle;
        background: #1a202c;
        border: solid #414868;
        margin: 0 1;
        padding: 1;
        layout: vertical;
        height: 5;
    }

    MostRecentPairDisplay > Label {
        color: #565f89;
        text-style: italic bold;
        margin: 0 1;
    }

    MostRecentPairDisplay > Static {
        color: #c0caf5;
        margin: 0 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pair_label = Label("Most Recent Pair", classes="label")
        self._details_label = Static("Waiting for data...", classes="details")

    def compose(self):
        yield self._pair_label
        yield self._details_label

    def update_pair(self, key1: str, key2: str, overlap_ms: float, status: str):
        """Update the display with a new key pair.

        Args:
            key1: First key in the pair
            key2: Second key in the pair
            overlap_ms: Overlap duration in milliseconds
            status: Status indicator (e.g., "PASS" or "FAIL")
        """
        self._details_label.update(
            f"[bold cyan]Pair:[/bold cyan] [{key1.upper()}] → [{key2.upper()}]\n"
            f"[bold yellow]Overlap:[/bold yellow] {overlap_ms:.0f}ms ({status})"
        )

    def clear(self):
        """Clear the display."""
        self._details_label.update("Waiting for data...")


class HotspotsDisplay(Vertical):
    """Display for top hotspot key pairs."""

    DEFAULT_CSS = """
    HotspotsDisplay {
        width: 1fr;
        content-align: left top;
        background: #1a202c;
        border: solid #414868;
        margin: 0 1;
        padding: 1;
        layout: vertical;
        height: 5;
    }

    HotspotsDisplay > Label {
        color: #565f89;
        text-style: italic bold;
        margin: 0 1;
    }

    HotspotsDisplay > Static {
        color: #c0caf5;
        margin: 0 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._title_label = Label("Adhesion Hotspots (Top 3)", classes="label")
        self._hotspots_label = Static("No hotspots yet...", classes="hotspots")

    def compose(self):
        yield self._title_label
        yield self._hotspots_label

    def update_hotspots(self, hotspots: list):
        """Update the display with new hotspot data.

        Args:
            hotspots: List of KeyInteraction objects
        """
        if not hotspots:
            self._hotspots_label.update("No hotspots yet...")
            return

        text_lines = []
        for i, hotspot in enumerate(hotspots, 1):
            key1, key2 = hotspot.key1, hotspot.key2
            overlap_ms = hotspot.overlap_duration * 1000
            percentage = hotspot.overlap_percentage

            line = f"{i}. [{key1.upper()}] & [{key2.upper()}]: {percentage:.0f}%"
            text_lines.append(line)

        self._hotspots_label.update("\n".join(text_lines))

    def clear(self):
        """Clear the display."""
        self._hotspots_label.update("No hotspots yet...")


class StatsPanel(Horizontal):
    """Universal statistics display panel."""

    DEFAULT_CSS = """
    StatsPanel {
        layout: horizontal;
        height: 5;
        margin: 1 0;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self):
        """Compose the stats panel."""
        yield MostRecentPairDisplay(id="most-recent-pair")
        yield HotspotsDisplay(id="hotspots")

    def update_universal_stats(self, recent_interaction, hotspots: list):
        """Update universal statistics display.

        Args:
            recent_interaction: Most recent KeyInteraction object (or None)
            hotspots: List of KeyInteraction objects
        """
        if recent_interaction:
            overlap_ms = recent_interaction.overlap_duration * 1000
            status = "FAIL" if overlap_ms > 50 else "PASS"
            self.query_one("#most-recent-pair", MostRecentPairDisplay).update_pair(
                recent_interaction.key1,
                recent_interaction.key2,
                overlap_ms,
                status
            )
        else:
            self.query_one("#most-recent-pair", MostRecentPairDisplay).clear()

        self.query_one("#hotspots", HotspotsDisplay).update_hotspots(hotspots)

    def clear(self):
        """Clear all displays."""
        self.query_one("#most-recent-pair", MostRecentPairDisplay).clear()
        self.query_one("#hotspots", HotspotsDisplay).clear()
