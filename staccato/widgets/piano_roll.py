"""Dynamic piano roll widget for Staccato v3.0."""

from textual.widget import Widget
from collections import deque
from staccato.events import KeyEvent
from staccato.constants import CANONICAL_KEY_ORDER, VIEW_WINDOW_SECONDS, VIEW_RESOLUTION, TIMELINE_BLOCK_WIDTH
import time
import sys

from loguru import logger

logger.remove()
logger.add("logs/piano_roll.log", rotation="10 MB", retention="1 day", level="DEBUG")


class PianoRollWidget(Widget):
    """Dynamic piano roll visualization.

    Shows only active keys in the current view window, sorted by HHKB layout.
    Uses atomic snapshot to prevent tearing during rendering.
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
        super().__init__(**kwargs)
        self.events = deque(maxlen=max_events)
        self.max_events = max_events
        self.active_keys = {}

        # Snapshot for atomic rendering
        self._events_snapshot = []
        self._active_keys_snapshot = {}
        self._snapshot_timestamp = 0.0

    def add_event(self, event: KeyEvent):
        logger.debug(f"[ADD_EVENT] key={event.key}, type={event.event_type}, timestamp={event.timestamp:.3f}")

        if event.event_type == 'press':
            # Ignore key repeat events (key already pressed)
            if event.key in self.active_keys:
                logger.debug(f"[REPEAT] Ignoring key repeat for {event.key}")
                return  # Skip repeat events

            self.active_keys[event.key] = event.timestamp
            logger.debug(f"[PRESS] Added to active_keys: {event.key} = {event.timestamp:.3f}")

        elif event.event_type == 'release':
            if event.key in self.active_keys:
                del self.active_keys[event.key]
                logger.debug(f"[RELEASE] Removed from active_keys: {event.key}")
            else:
                logger.debug(f"[RELEASE] Key {event.key} not in active_keys (already released or repeat)")
                return  # Skip if not in active_keys

        # Only add to events if we didn't return early
        self.events.append(event)
        self.refresh()

    def _create_snapshot(self):
        """Create an atomic snapshot of current state for rendering."""
        self._events_snapshot = list(self.events)
        self._active_keys_snapshot = dict(self.active_keys)
        self._snapshot_timestamp = time.perf_counter()
        
        logger.debug(f"[SNAPSHOT] Created at timestamp={self._snapshot_timestamp:.3f}, "
                     f"events={len(self._events_snapshot)}, active_keys={list(self._active_keys_snapshot.keys())}")

    def _get_active_keys_in_window(self, view_start, view_end):
        """Get active keys from snapshot."""
        keys = set()
        for event in self._events_snapshot:
            if view_start <= event.timestamp <= view_end:
                keys.add(event.key)
        return keys

    def _sort_keys_by_canonical_order(self, keys):
        """Sort keys by HHKB canonical order."""
        def get_sort_order(key):
            return CANONICAL_KEY_ORDER.get(key.lower(), 1000)

        return sorted(keys, key=get_sort_order)

    def _calculate_key_timeline(self, key, view_start, view_end):
        """Calculate timeline blocks for a specific key."""
        num_blocks = TIMELINE_BLOCK_WIDTH
        timeline = []

        press_times = []

        # Collect all press/release pairs using queue
        from collections import deque
        pending_presses = deque()

        logger.debug(f"[TIMELINE] key={key}, view_start={view_start:.3f}, view_end={view_end:.3f}")

        for event in self._events_snapshot:
            if event.key != key:
                continue

            if event.event_type == 'press':
                pending_presses.append(event.timestamp)
                logger.debug(f"[TIMELINE] Press queued at {event.timestamp:.3f}, queue_size={len(pending_presses)}")
            elif event.event_type == 'release':
                if pending_presses:
                    press_time = pending_presses.popleft()
                    press_times.append((press_time, event.timestamp))
                    logger.debug(f"[TIMELINE] Matched press={press_time:.3f} to release={event.timestamp:.3f}")
                else:
                    logger.debug(f"[TIMELINE] Release at {event.timestamp:.3f} has no matching press!")

        # Handle currently pressed key (long press)
        if key.lower() in self._active_keys_snapshot:
            press_time = self._active_keys_snapshot[key.lower()]
            logger.debug(f"[TIMELINE] Key {key} is currently pressed at {press_time:.3f}")
            
            # Check if this press is already matched
            already_matched = False
            for ps, pe in press_times:
                if abs(ps - press_time) < 0.001:
                    already_matched = True
                    break
            
            if not already_matched:
                if press_time >= view_start:
                    press_times.append((press_time, view_end))
                    logger.debug(f"[TIMELINE] Added ongoing press: {press_time:.3f} -> {view_end:.3f}")
                else:
                    press_times.append((view_start, view_end))
                    logger.debug(f"[TIMELINE] Added extended press: {view_start:.3f} -> {view_end:.3f}")
            else:
                logger.debug(f"[TIMELINE] Press at {press_time:.3f} already matched, skipping")
        else:
            logger.debug(f"[TIMELINE] Key {key} is NOT in active_keys_snapshot")

        # For each block, check if any press interval overlaps
        for i in range(num_blocks):
            block_start = view_start + (i * VIEW_RESOLUTION)
            block_end = block_start + VIEW_RESOLUTION

            block_active = False
            for press_start, press_end in press_times:
                # Check overlap: press interval overlaps with block if ANY part of press is in block
                # More permissive: count block if press starts before block ends AND ends after block starts
                if press_start < block_end and press_end > block_start:
                    block_active = True
                    break

            timeline.append('█' if block_active else ' ')

        filled_count = timeline.count('█')
        logger.debug(f"[TIMELINE] key={key}, filled_blocks={filled_count}/100, press_times={press_times}")

        return ''.join(timeline)

    def render(self):
        """Render the piano roll using atomic snapshot."""
        from rich.text import Text

        self._create_snapshot()

        current_time = self._snapshot_timestamp
        view_start = current_time - VIEW_WINDOW_SECONDS
        view_end = current_time

        logger.debug(f"[RENDER] Starting render at time={current_time:.3f}, view=[{view_start:.3f}, {view_end:.3f}]")

        active_keys = self._get_active_keys_in_window(view_start, view_end)

        text = Text()
        text.append("DYNAMIC PIANO ROLL\n", style="bold #7aa2f7")
        text.append("=" * 70 + "\n\n", style="dim")

        if not active_keys:
            last_activity = None
            if self._events_snapshot:
                last_activity = current_time - self._events_snapshot[-1].timestamp

            if last_activity is not None:
                text.append(f"Last activity: {last_activity:.1f}s ago\n", style="dim")
            else:
                text.append("Waiting for key events...\n", style="dim")

            text.append("\n", style="dim")
            text.append(f"View Window: {VIEW_WINDOW_SECONDS}s | ", style="dim")
            text.append(f"Resolution: {VIEW_RESOLUTION*1000:.0f}ms/block", style="dim")

            logger.debug(f"[RENDER] No active keys, last_activity={last_activity}")
            return text

        sorted_keys = self._sort_keys_by_canonical_order(active_keys)
        logger.debug(f"[RENDER] Rendering {len(sorted_keys)} keys: {sorted_keys}")

        max_label_length = 12
        for key in sorted_keys:
            label = key.upper()
            if len(label) > max_label_length:
                label = label[:max_label_length]

            text.append(f"{label.ljust(max_label_length)} | ", style="bold cyan")

            timeline = self._calculate_key_timeline(key, view_start, view_end)
            text.append(timeline, style="bold #7aa2f7")

            text.append(" | ", style="dim")

            if key.lower() in self._active_keys_snapshot:
                press_duration = current_time - self._active_keys_snapshot[key.lower()]
                text.append(f"● {press_duration:.2f}s", style="bold green")
            else:
                text.append("○ released", style="dim")

            text.append("\n")

        text.append("\n", style="dim")
        text.append("-" * 70, style="dim")
        text.append(" Time (", style="dim")
        text.append(f"{-VIEW_WINDOW_SECONDS:.0f}s", style="bold #7aa2f7")
        text.append(" → now)", style="dim")
        text.append("\n\n", style="dim")
        text.append(f"Active Keys: {len(sorted_keys)}  ", style="bold yellow")
        text.append(f"Total Events: {len(self._events_snapshot)}", style="dim")

        logger.debug(f"[RENDER] Complete, total events in snapshot: {len(self._events_snapshot)}")
        return text

    def clear(self):
        self.events.clear()
        self.active_keys.clear()
        self._events_snapshot = []
        self._active_keys_snapshot = {}
        self._snapshot_timestamp = 0.0
        self.refresh()
