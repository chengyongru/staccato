"""Event log widget for Staccato."""

from textual.widgets import RichLog
from staccato.events import KeyEvent
from collections import deque
import time

from staccato.logger import get_logger

logger = get_logger("EVENT_LOG")

def _log_debug(msg):
    logger.debug(msg)

def _log_warning(msg):
    logger.warning(msg)


class EventLog(RichLog):
    """Scrollable log of keyboard events."""

    DEFAULT_CSS = """
    EventLog {
        background: #151922;
        border: solid #414868;
        min-height: 10;
        height: 1fr;
        overflow-y: auto;
        padding: 0 1 1 1;
        scrollbar-gutter: stable;
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
        super().__init__(max_lines=max_lines, auto_scroll=True, **kwargs)
        self.max_lines = max_lines
        self.wrap = True
        self._events_history = deque(maxlen=max_lines)
        self._session_start = None

    def log_event(self, event: KeyEvent, active_keys=None):
        """Log a keyboard event.

        Args:
            event: KeyEvent to log
            active_keys: Optional dict of currently active keys
        """
        from rich.text import Text

        if self._session_start is None:
            self._session_start = event.timestamp

        rel_time = event.timestamp - self._session_start
        key = event.key.lower()

        _log_debug(f"[EVENT_LOG] {event.event_type.upper()} {event.key}: rel_time={rel_time:.3f}s")

        if event.event_type == 'press':
            self._log_press(rel_time, event.key)
        elif event.event_type == 'release':
            duration = 0
            if active_keys is not None and key in active_keys:
                duration = event.timestamp - active_keys[key]
            self._log_release(rel_time, event.key, duration)

        self._events_history.append(event)
        
        # Force immediate UI update
        self.refresh(layout=True)
        # Ensure we scroll to the latest entry
        self.call_after_refresh(self.scroll_end)

    def _format_time(self, seconds: float) -> str:
        """Format seconds into human readable time."""
        if seconds < 1:
            return f"{seconds*1000:5.0f}ms"
        elif seconds < 60:
            return f"{seconds:5.2f}s"
        else:
            mins = int(seconds // 60)
            secs = seconds % 60
            return f"{mins:02d}:{secs:05.2f}"

    def _log_press(self, rel_time: float, key: str):
        """Log a key press event."""
        from rich.text import Text

        time_str = self._format_time(rel_time)
        text = Text()
        text.append(f"{time_str:>8}  ", style="dim #a9b1d6")
        text.append("▼", style="bold #7aa2f7")
        text.append("  ", style="dim")
        text.append(f"{key.upper():<6}", style="bold cyan")
        text.append("  PRESS", style="dim #7aa2f7")

        self.write(text)

    def _log_release(self, rel_time: float, key: str, duration: float):
        """Log a key release event."""
        from rich.text import Text

        time_str = self._format_time(rel_time)
        duration_str = self._format_time(duration)
        text = Text()
        text.append(f"{time_str:>8}  ", style="dim #a9b1d6")
        text.append("▲", style="bold #9ece6a")
        text.append("  ", style="dim")
        text.append(f"{key.upper():<6}", style="bold yellow")
        text.append("  RELEASE  ", style="dim #9ece6a")
        text.append(f"[{duration_str}]", style="italic #a9b1d6")

        self.write(text)

    def _log_release_unknown(self, rel_time: float, key: str):
        """Log a release event for unknown key."""
        from rich.text import Text

        time_str = self._format_time(rel_time)
        text = Text()
        text.append(f"{time_str:>8}  ", style="dim #a9b1d6")
        text.append("▲", style="bold #f7768e")
        text.append("  ", style="dim")
        text.append(f"{key.upper():<6}", style="dim #f7768e")
        text.append("  (no press)", style="dim red")

        self.write(text)

    def log_release_with_duration(self, event: KeyEvent, duration: float):
        """Log a key release event with known duration.

        Args:
            event: KeyEvent to log
            duration: Press duration in seconds
        """
        from rich.text import Text

        if self._session_start is None:
            self._session_start = event.timestamp

        rel_time = event.timestamp - self._session_start
        key = event.key.lower()

        _log_debug(f"[EVENT_LOG] RELEASE {event.key}: rel_time={rel_time:.3f}s, duration={duration:.3f}s")

        self._log_release(rel_time, event.key, duration)
        self._events_history.append(event)
        
        # Force immediate UI update
        self.refresh(layout=True)
        self.call_after_refresh(self.scroll_end)

    def log_message(self, message: str):
        """Log a general message.

        Args:
            message: Message to log
        """
        from rich.text import Text
        text = Text(message, style="dim")
        self.write(text)
        self.refresh(layout=True)
        self.call_after_refresh(self.scroll_end)

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
        self.refresh(layout=True)
        self.call_after_refresh(self.scroll_end)

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
        self.refresh(layout=True)
        self.call_after_refresh(self.scroll_end)

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
        self.refresh(layout=True)
        self.call_after_refresh(self.scroll_end)
