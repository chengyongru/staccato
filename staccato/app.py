"""Main application for Staccato."""

import time
import queue
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static
from textual.containers import Horizontal, Vertical
from textual import work

from staccato.collector import KeyboardCollector
from staccato.events import KeyEvent, KeySession
from staccato.session import SessionManager
from staccato.analyzer import TimingAnalyzer
from staccato.widgets.stats_panel import StatsPanel
from staccato.widgets.event_log import EventLog
from staccato.widgets.piano_roll import PianoRollWidget
from staccato.key_tracker import KeyStateTracker

from staccato.logger import get_logger

logger = get_logger("APP")

# Time window for live event statistics (seconds)
LIVE_EVENT_WINDOW_SECONDS = 10.0


class StaccatoApp(App):
    """Main Staccato application."""

    # Get absolute path to CSS file relative to this file
    _CSS_FILE = Path(__file__).parent / "styles" / "default.tcss"
    CSS_PATH = str(_CSS_FILE)
    TITLE = "Staccato - Input Micro-timing Analyzer"
    
    # Enable double buffering and optimize rendering
    ENABLE_COMMAND_PALETTE = False  # Reduce unnecessary UI overhead

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Thread-safe data structures
        self.event_queue = queue.Queue(maxsize=1000)
        self.collector = KeyboardCollector(self)
        self.session_manager = SessionManager()
        self.analyzer = TimingAnalyzer()
        self.key_tracker = KeyStateTracker()

        # State
        self.is_recording = False
        self.current_session = None
        # Live statistics (always updated, even when not recording)
        self.live_events = []  # Keep track of all events for real-time stats

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()

        with Vertical(id="main"):
            yield StatsPanel()
            yield PianoRollWidget()
            yield EventLog()

        with Horizontal(id="controls"):
            yield Button("Start Recording", id="btn-record", variant="primary")
            yield Button("Stop Recording", id="btn-stop", variant="warning")
            yield Button("Save Session", id="btn-save")
            yield Button("Load Session", id="btn-load")
            yield Button("Clear", id="btn-clear")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize app on mount."""
        # Register listeners with key tracker
        piano_roll = self.query_one(PianoRollWidget)
        event_log = self.query_one(EventLog)

        self.key_tracker.add_listener(lambda e, keys: piano_roll.add_event(e, keys))
        self.key_tracker.add_listener(lambda e, keys: event_log.log_event(e, keys))

        # Start keyboard listener using keyboard library
        logger.info("[APP] Starting keyboard collector...")
        try:
            self.collector.start()
            logger.info("[APP] Keyboard collector started successfully")
        except Exception as e:
            logger.error(f"[APP] Failed to start keyboard collector: {e}")
            import traceback
            logger.error(traceback.format_exc())

        # Start UI update loop (20fps is sufficient for TUI and reduces flicker)
        # Higher FPS causes more frequent re-renders which can cause flicker in terminals
        self.set_interval(1/20, self.update_ui)

        # Start stats calculation (every second)
        self.set_interval(1, self.calculate_stats)

    def on_unmount(self) -> None:
        """Clean up when app is closing."""
        # Stop keyboard listener
        self.collector.stop()

    def update_ui(self) -> None:
        """20fps UI update - processes queued events and updates UI."""
        # Process all pending events
        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                self.process_event(event)
            except queue.Empty:
                break

        # Always refresh piano roll to allow time-based scrolling
        # The piano roll's internal diffing mechanism prevents unnecessary re-renders
        piano_roll = self.query_one(PianoRollWidget)
        piano_roll.refresh()

    def process_event(self, event: KeyEvent):
        """Process a single keyboard event."""
        logger.debug(f"[APP] process_event: key={event.key}, type={event.event_type}, timestamp={event.timestamp:.3f}")

        # Add to current session if recording
        if self.is_recording and self.current_session:
            self.current_session.events.append(event)

        # Always add to live events for real-time statistics
        self.live_events.append(event)

        # Keep only last N seconds of live events for stats
        current_time = event.timestamp
        self.live_events = [
            e for e in self.live_events
            if current_time - e.timestamp <= LIVE_EVENT_WINDOW_SECONDS
        ]

        # Process event through centralized key tracker
        processed = self.key_tracker.process_event(event)

        if not processed:
            logger.debug(f"[APP] Event {event.key} ({event.event_type}) was filtered out by key tracker")
            return

    def calculate_stats(self):
        """Calculate and display universal statistics every second."""
        events = self.live_events if self.live_events else []

        if not events:
            return

        metrics = self.analyzer.analyze_session(events)

        if not metrics:
            return

        # Calculate session metrics
        session_metrics = self.analyzer.calculate_session_metrics(metrics)

        # Get recent interaction and hotspots
        recent_interaction = self.analyzer.get_most_recent_pair_overlap(metrics)
        hotspots = self.analyzer.find_hotspot_overlaps(metrics, top_n=5)

        # Update stats panel with new metrics
        self.query_one(StatsPanel).update_universal_stats(
            recent_interaction, hotspots, session_metrics
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn-record":
            self.start_recording()
        elif button_id == "btn-stop":
            self.stop_recording()
        elif button_id == "btn-save":
            self.save_session()
        elif button_id == "btn-load":
            self.load_session()
        elif button_id == "btn-clear":
            self.clear_session()

    def start_recording(self):
        """Start recording a new session."""
        self.is_recording = True
        self.current_session = KeySession()
        self.current_session.start_time = time.perf_counter()

        self.query_one(EventLog).log_success("Recording started...")
        self.query_one("#btn-record").display = False
        self.query_one("#btn-stop").display = True

    def stop_recording(self):
        """Stop recording."""
        self.is_recording = False
        if self.current_session:
            self.current_session.end_time = time.perf_counter()

        event_count = len(self.current_session.events) if self.current_session else 0
        self.query_one(EventLog).log_success(
            f"Recording stopped. Captured {event_count} events."
        )
        self.query_one("#btn-record").display = True
        self.query_one("#btn-stop").display = False

    def save_session(self):
        """Save current session to file."""
        if not self.current_session or not self.current_session.events:
            self.query_one(EventLog).log_warning("No session to save.")
            return

        filepath = self.session_manager.save_session(self.current_session)
        self.query_one(EventLog).log_success(f"Session saved to {filepath}")

    def load_session(self):
        """Load session from file."""
        # For now, just log placeholder
        self.query_one(EventLog).log_message("Load session: feature coming soon")

    def clear_session(self):
        """Clear current session."""
        self.current_session = None
        self.live_events = []
        self.key_tracker.clear()
        self.query_one(PianoRollWidget).clear()
        self.query_one(EventLog).clear()
        self.query_one(StatsPanel).clear()
        self.query_one(EventLog).log_message("Session cleared.")


def main() -> None:
    """Entry point for Staccato application."""
    app = StaccatoApp()
    app.run()
