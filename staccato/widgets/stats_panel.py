"""Signal Hygiene Dashboard for Staccato v3.0."""

from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Label


class SessionScoreDisplay(Vertical):
    """Display for overall signal hygiene score."""

    DEFAULT_CSS = """
    SessionScoreDisplay {
        width: 25%;
        min-width: 20;
        background: #1a202c;
        border: solid #7aa2f7;
        padding: 1;
        layout: vertical;
        content-align: center middle;
        height: 10;
    }

    SessionScoreDisplay.excellent { border: solid #9ece6a; }
    SessionScoreDisplay.good { border: solid #e0af68; }
    SessionScoreDisplay.fair { border: solid #ff9e64; }
    SessionScoreDisplay.poor { border: solid #f7768e; }

    SessionScoreDisplay > Label {
        color: #565f89;
        text-style: italic bold;
        margin: 0 1;
    }

    SessionScoreDisplay > Static {
        color: #c0caf5;
        margin: 0 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._title_label = Label("SIGNAL HYGIENE", classes="label")
        self._score_label = Static("--", classes="score")
        self._status_label = Static("Waiting...", classes="status")

    def compose(self):
        yield self._title_label
        yield self._score_label
        yield self._status_label

    def update_score(self, metrics):
        """Update the display with session metrics.

        Args:
            metrics: SessionMetrics object
        """
        score = int(metrics.hygiene_score)
        self._score_label.update(f"[bold cyan]{score}[/bold cyan]")

        # Determine status and color
        # Remove all existing classes first
        self.remove_class("excellent")
        self.remove_class("good")
        self.remove_class("fair")
        self.remove_class("poor")

        if score >= 80:
            status = "EXCELLENT"
            self.set_class(True, "excellent")
        elif score >= 60:
            status = "GOOD"
            self.set_class(True, "good")
        elif score >= 40:
            status = "FAIR"
            self.set_class(True, "fair")
        else:
            status = "POOR"
            self.set_class(True, "poor")

        self._status_label.update(f"[bold]{status}[/bold]")

    def clear(self):
        """Clear the display."""
        self._score_label.update("--")
        self._status_label.update("Waiting...")
        self.remove_class("excellent")
        self.remove_class("good")
        self.remove_class("fair")
        self.remove_class("poor")


class SignalQualityBreakdown(Vertical):
    """Display for signal quality breakdown with severity distribution."""

    DEFAULT_CSS = """
    SignalQualityBreakdown {
        width: 40%;
        background: #1a202c;
        border: solid #414868;
        margin: 0 1;
        padding: 1;
        layout: vertical;
        height: 10;
    }

    SignalQualityBreakdown > Label {
        color: #565f89;
        text-style: italic bold;
        margin: 0 1;
    }

    SignalQualityBreakdown > Static {
        color: #c0caf5;
        margin: 0 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._title_label = Label("SIGNAL QUALITY", classes="label")
        self._breakdown_label = Static("Waiting for data...", classes="breakdown")

    def compose(self):
        yield self._title_label
        yield self._breakdown_label

    def update_breakdown(self, metrics):
        """Update the display with session metrics.

        Args:
            metrics: SessionMetrics object
        """
        # Calculate actual clean percentage (independent keypresses / total keypresses)
        clean_pct = int((metrics.clean_keypresses / metrics.total_keypresses * 100)
                       if metrics.total_keypresses > 0 else 100)

        # Create visual bar
        bar_length = int(clean_pct / 10)
        bar = "█" * bar_length + "░" * (10 - bar_length)

        lines = [
            f"[bold cyan]{bar}[/bold cyan] [bold]{clean_pct}%[/bold] Clean",
            f"",
            f"[#9ece6a]Independent:[/#9ece6a] {metrics.clean_keypresses}",
            f"[#e0af68]Minor:[/#e0af68] {metrics.minor_adhesions}",
            f"[#ff9e64]Moderate:[/#ff9e64] {metrics.moderate_adhesions}",
            f"[#f7768e]Severe:[/#f7768e] {metrics.severe_adhesions}",
        ]

        self._breakdown_label.update("\n".join(lines))

    def clear(self):
        """Clear the display."""
        self._breakdown_label.update("Waiting for data...")


class WorstOffendersDisplay(Vertical):
    """Display for top problematic key pairs with severity indicators."""

    DEFAULT_CSS = """
    WorstOffendersDisplay {
        width: 35%;
        background: #1a202c;
        border: solid #414868;
        margin: 0 1;
        padding: 1;
        layout: vertical;
        height: 10;
    }

    WorstOffendersDisplay > Label {
        color: #565f89;
        text-style: italic bold;
        margin: 0 1;
    }

    WorstOffendersDisplay > Static {
        color: #c0caf5;
        margin: 0 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._title_label = Label("WORST OFFENDERS (Top 5)", classes="label")
        self._offenders_label = Static("No data yet...", classes="offenders")

    def compose(self):
        yield self._title_label
        yield self._offenders_label

    def update_offenders(self, hotspots):
        """Update the display with hotspot data.

        Args:
            hotspots: List of KeyInteraction objects
        """
        if not hotspots:
            self._offenders_label.update("No data yet...")
            return

        text_lines = []
        for i, hotspot in enumerate(hotspots, 1):
            key1, key2 = hotspot.key1, hotspot.key2
            overlap_ms = hotspot.overlap_duration * 1000

            # Determine severity
            if overlap_ms < 50:
                severity = "[#e0af68]MINOR[#e0af68]"
            elif overlap_ms < 100:
                severity = "[#ff9e64]MODERATE[#ff9e64]"
            else:
                severity = "[#f7768e]SEVERE[#f7768e]"

            line = f"{i}. [{key1.upper()}]+[{key2.upper()}]: {int(overlap_ms)}ms {severity}"
            text_lines.append(line)

        self._offenders_label.update("\n".join(text_lines))

    def clear(self):
        """Clear the display."""
        self._offenders_label.update("No data yet...")


class StatsPanel(Horizontal):
    """Signal Hygiene Dashboard - universal statistics display panel."""

    DEFAULT_CSS = """
    StatsPanel {
        layout: horizontal;
        min-height: 5;
        height: auto;
        margin: 1 0;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self):
        """Compose the stats panel."""
        yield SessionScoreDisplay(id="session-score")
        yield SignalQualityBreakdown(id="signal-quality")
        yield WorstOffendersDisplay(id="worst-offenders")

    def update_universal_stats(self, recent_interaction, hotspots, session_metrics):
        """Update universal statistics display.

        Args:
            recent_interaction: Most recent KeyInteraction object (or None) - kept for compatibility
            hotspots: List of KeyInteraction objects
            session_metrics: SessionMetrics object
        """
        # Update session score
        self.query_one("#session-score", SessionScoreDisplay).update_score(session_metrics)

        # Update signal quality breakdown
        self.query_one("#signal-quality", SignalQualityBreakdown).update_breakdown(session_metrics)

        # Update worst offenders
        self.query_one("#worst-offenders", WorstOffendersDisplay).update_offenders(hotspots)

    def clear(self):
        """Clear all displays."""
        self.query_one("#session-score", SessionScoreDisplay).clear()
        self.query_one("#signal-quality", SignalQualityBreakdown).clear()
        self.query_one("#worst-offenders", WorstOffendersDisplay).clear()
