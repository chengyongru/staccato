"""Event log widget for Staccato."""

from textual.widgets import RichLog
from staccato.events import KeyEvent


class EventLog(RichLog):
    """Scrollable log of keyboard events."""

    DEFAULT_CSS = """
    EventLog {
        background: #151922;
        border: solid #414868;
        height: 12;
        overflow-y: auto;
        padding: 1;
    }

    EventLog RichLog {
        scrollbar-background: #0a0e14;
        scrollbar-color: #7aa2f7;
    }
    """

    def __init__(self, max_lines: int = 1000, **kwargs):
        """Initialize event log.

        Args:
            max_lines: Maximum number of lines to keep in history
        """
        super().__init__(**kwargs)
        self.max_lines = max_lines
        self.wrap = True

    def log_event(self, event: KeyEvent):
        """Log a keyboard event.

        Args:
            event: KeyEvent to log
        """
        from rich.text import Text

        time_str = f"{event.timestamp:.3f}"
        icon = "⬇" if event.event_type == "press" else "⬆"

        # Create Text object with styling
        text = Text()
        text.append(time_str, style="dim")
        text.append(" ")
        text.append(icon, style=f"{'blue' if event.event_type == 'press' else 'dim'} bold")
        text.append(" ")
        text.append(event.key.upper())
        text.append(f" @{event.timestamp:.3f}", style="dim")

        self.write(text)

    def log_message(self, message: str):
        """Log a general message.

        Args:
            message: Message to log
        """
        from rich.text import Text
        text = Text(message, style="dim")
        self.write(text)

    def log_success(self, message: str):
        """Log a success message.

        Args:
            message: Message to log
        """
        from rich.text import Text
        text = Text()
        text.append("✓ ", style="green")
        text.append(message)
        self.write(text)

    def log_warning(self, message: str):
        """Log a warning message.

        Args:
            message: Message to log
        """
        from rich.text import Text
        text = Text()
        text.append("⚠ ", style="yellow")
        text.append(message)
        self.write(text)

    def log_error(self, message: str):
        """Log an error message.

        Args:
            message: Message to log
        """
        from rich.text import Text
        text = Text()
        text.append("✗ ", style="red")
        text.append(message)
        self.write(text)
