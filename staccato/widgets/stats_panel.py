"""Statistics display panel for Staccato."""

from textual.containers import Horizontal
from textual.widgets import Static, Label, Digits


class StatsItem(Horizontal):
    """A single statistics item container."""

    DEFAULT_CSS = """
    StatsItem {
        width: 1fr;
        content-align: center middle;
        background: #1a202c;
        border: solid #414868;
        margin: 0 1;
        padding: 1 2;
        layout: vertical;
        height: 5;
    }

    StatsItem > Label {
        color: #565f89;
        text-style: italic;
        margin: 0 1;
    }

    StatsItem > Digits {
        color: #7aa2f7;
        text-style: bold;
        margin: 0 1;
    }
    """

    def __init__(self, label_text: str, initial_value: str = "0", **kwargs):
        """Initialize stats item.

        Args:
            label_text: Text for the label
            initial_value: Initial value for the digits display
        """
        super().__init__(**kwargs)
        self._label_text = label_text
        self._initial_value = initial_value

    def compose(self):
        """Compose the stats item."""
        yield Label(self._label_text, classes="label")
        yield Digits(self._initial_value)


class StatsPanel(Horizontal):
    """Statistics display panel."""

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
        yield StatsItem("Total Keys", "0", id="total-keys-item")
        yield StatsItem("KPS", "0.0", id="kps-item")
        yield StatsItem("Avg Duration", "0ms", id="avg-duration-item")
        yield StatsItem("Overlaps", "0", id="overlaps-item")

    def update_stats(self, total: int, kps: float, avg: float, overlaps: int):
        """Update statistics display.

        Args:
            total: Total number of key presses
            kps: Keys per second
            avg: Average duration in milliseconds
            overlaps: Number of detected overlaps
        """
        # Query the Digits widget within each StatsItem
        self.query_one("#total-keys-item Digits").update(str(total))
        self.query_one("#kps-item Digits").update(f"{kps:.1f}")
        self.query_one("#avg-duration-item Digits").update(f"{avg:.0f}ms")
        self.query_one("#overlaps-item Digits").update(str(overlaps))
