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


class StaccatoApp(App):
    """Main Staccato application."""

    # Get absolute path to CSS file relative to this file
    _CSS_FILE = Path(__file__).parent / "styles" / "default.tcss"
    CSS_PATH = str(_CSS_FILE)
    TITLE = "Staccato - Input Micro-timing Analyzer"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Thread-safe data structures
        self.event_queue = queue.Queue(maxsize=1000)
        self.collector = KeyboardCollector(self)
        self.session_manager = SessionManager()
        self.analyzer = TimingAnalyzer()

        # State
        self.is_recording = False
        self.current_session = None
        # Live statistics (always updated, even when not recording)
        self.live_events = []  # Keep track of all events for real-time stats

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()

        yield Static(" [bold]Staccato[/bold] - Input Micro-timing Analyzer ", classes="header")

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
        # Start keyboard listener using keyboard library
        self.collector.start()

        # Start 60fps update loop
        self.set_interval(1/60, self.update_ui)

        # Start stats calculation (every second)
        self.set_interval(1, self.calculate_stats)

    def _run_keyboard_listener(self):
        """Run keyboard listener in background thread."""
        # Start keyboard listener
        self.collector.start()

    def on_unmount(self) -> None:
        """Clean up when app is closing."""
        # Stop keyboard listener
        self.collector.stop()

    def update_ui(self):
        """60fps UI update - processes queued events."""
        # Process all pending events
        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                self.process_event(event)
            except queue.Empty:
                break

        # Update piano roll visualization
        self.query_one(PianoRollWidget).refresh()

    def process_event(self, event: KeyEvent):
        """Process a single keyboard event."""
        # Add to current session if recording
        if self.is_recording and self.current_session:
            self.current_session.events.append(event)

        # Always add to live events for real-time statistics
        self.live_events.append(event)

        # Keep only last 10 seconds of live events for stats
        current_time = event.timestamp
        self.live_events = [
            e for e in self.live_events
            if current_time - e.timestamp <= 10.0
        ]

        # Update piano roll
        self.query_one(PianoRollWidget).add_event(event)

        # Force immediate refresh for real-time responsiveness
        self.query_one(PianoRollWidget).refresh()

        # Update event log
        self.query_one(EventLog).log_event(event)

    def calculate_stats(self):
        """Calculate and display universal statistics every second."""
        events = self.live_events if self.live_events else []

        if not events:
            return

        metrics = self.analyzer.analyze_session(events)

        if not metrics:
            return

        recent_interaction = self.analyzer.get_most_recent_pair_overlap(metrics)
        hotspots = self.analyzer.find_hotspot_overlaps(metrics, top_n=3)

        self.query_one(StatsPanel).update_universal_stats(
            recent_interaction, hotspots
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

        self.query_one(EventLog).log_success(
            f"Recording stopped. Captured {len(self.current_session.events)} events."
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
        self.query_one(PianoRollWidget).clear()
        self.query_one(EventLog).clear()
        self.query_one(StatsPanel).clear()
        self.query_one(EventLog).log_message("Session cleared.")
