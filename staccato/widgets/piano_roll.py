"""Piano roll widget for Staccato."""

from textual.widget import Widget
from textual.reactive import var
from collections import deque
from staccato.events import KeyEvent
import time


class PianoRollWidget(Widget):
    """Real-time key status visualization.

    Shows which keys are currently pressed and recent activity.
    """

    DEFAULT_CSS = """
    PianoRollWidget {
        background: #1a202c;
        border: solid #7aa2f7;
        height: 20;
        margin: 1 0;
        padding: 1;
    }
    """

    def __init__(self, max_events: int = 1000, **kwargs):
        """Initialize piano roll widget.

        Args:
            max_events: Maximum number of events to keep in history
        """
        super().__init__(**kwargs)
        self.events = deque(maxlen=max_events)
        self.max_events = max_events

        # Track currently pressed keys
        self.active_keys = {}  # key -> press_time

        # Common keys to display
        self.tracked_keys = list("asdfjkl;")

    def add_event(self, event: KeyEvent):
        """Add a new event to the timeline.

        Args:
            event: KeyEvent to add
        """
        self.events.append(event)

        # Update active keys tracking
        if event.event_type == 'press':
            self.active_keys[event.key] = event.timestamp
        elif event.event_type == 'release' and event.key in self.active_keys:
            del self.active_keys[event.key]

        self.refresh()

    def render(self):
        """Render the key status display."""
        from rich.text import Text
        from rich.table import Table

        # Create a table for better layout
        text = Text()

        # Header
        text.append("KEY STATUS MONITOR\n", style="bold #7aa2f7")
        text.append("=" * 70 + "\n\n", style="dim")

        # Show all tracked keys with their status
        for key in self.tracked_keys:
            key_lower = key.lower()
            is_active = key_lower in self.active_keys

            # Key label
            text.append(f"{key.upper():4}", style="bold cyan")

            # Status indicator
            if is_active:
                press_duration = time.perf_counter() - self.active_keys[key_lower]
                text.append(" ● PRESSED", style="bold green")
                text.append(f" ({press_duration:.2f}s)", style="dim")
            else:
                text.append(" ○ released", style="dim")

            text.append("\n")

        # Show summary
        text.append("\n", style="dim")
        text.append(f"Active Keys: {len(self.active_keys)}  ", style="bold yellow")
        text.append(f"Total Events: {len(self.events)}", style="dim")

        return text

    def clear(self):
        """Clear all events from the timeline."""
        self.events.clear()
        self.active_keys.clear()
        self.refresh()
