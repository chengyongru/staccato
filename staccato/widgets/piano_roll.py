"""Dynamic piano roll widget for Staccato v3.0."""

from textual.widget import Widget
from collections import deque
from staccato.events import KeyEvent
from staccato.constants import CANONICAL_KEY_ORDER, VIEW_WINDOW_SECONDS, VIEW_RESOLUTION, TIMELINE_BLOCK_WIDTH
import time
import sys

from staccato.logger import get_logger

logger = get_logger("PIANO_ROLL")


class PianoRollWidget(Widget):
    """Dynamic piano roll visualization.

    Shows only active keys in the current view window, sorted by HHKB layout.
    Uses atomic snapshot to prevent tearing during rendering.
    """

    DEFAULT_CSS = """
    PianoRollWidget {
        background: #1a202c;
        border: solid #7aa2f7;
        min-height: 15;
        height: 2fr;
        margin: 1 0;
        padding: 1;
    }
    """

    def __init__(self, max_events: int = 1000, **kwargs):
        super().__init__(**kwargs)
        self.events = deque(maxlen=max_events)
        self.max_events = max_events

        # Snapshot for atomic rendering
        self._events_snapshot = []
        self._snapshot_timestamp = 0.0

        # Navigation state
        self.view_offset = 0.0  # Time offset for navigation (in seconds)
        self._scroll_offset = 0  # Vertical scroll offset for key list

    def add_event(self, event: KeyEvent, active_keys=None):
        logger.debug(f"[ADD_EVENT] key={event.key}, type={event.event_type}, timestamp={event.timestamp:.3f}")

        self.events.append(event)
        self.refresh()

    def _create_snapshot(self):
        """Create an atomic snapshot of current state for rendering."""
        self._events_snapshot = list(self.events)
        self._snapshot_timestamp = time.perf_counter()

        logger.debug(f"[SNAPSHOT] Created at timestamp={self._snapshot_timestamp:.3f}, "
                     f"events={len(self._events_snapshot)}")

    def _get_active_keys_at_time(self, reference_time):
        """Calculate which keys should be active at a given reference time.

        This computes the active key state dynamically from the event snapshot,
        rather than relying on a stored snapshot that can become stale.

        Args:
            reference_time: The time point to check active keys at

        Returns:
            dict: Mapping of key -> press_timestamp for keys active at reference_time
        """
        active_keys = {}
        pending_presses = {}

        for event in self._events_snapshot:
            key = event.key.lower()

            if event.event_type == 'press':
                if key not in pending_presses:
                    pending_presses[key] = event.timestamp
            elif event.event_type == 'release':
                # Key released, remove from active keys
                if key in pending_presses:
                    del pending_presses[key]
                if key in active_keys:
                    del active_keys[key]

        # Any keys still in pending_presses at the end are still pressed
        active_keys = dict(pending_presses)

        logger.debug(f"[ACTIVE_KEYS_AT_TIME] time={reference_time:.3f}, active={list(active_keys.keys())}")
        return active_keys

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

    def _calculate_key_timeline(self, key, view_start, view_end, num_blocks=None, all_key_press_times=None):
        """Calculate timeline blocks for a specific key with overlap detection.

        Args:
            key: Key name
            view_start: Start of view window
            view_end: End of view window
            num_blocks: Number of timeline blocks (auto-calculated if None)
            all_key_press_times: Dict mapping key -> list of (press_start, press_end) tuples for overlap detection
        """
        if num_blocks is None:
            num_blocks = TIMELINE_BLOCK_WIDTH

        if all_key_press_times is None:
            all_key_press_times = {}

        timeline = []
        timeline_overlaps = []  # Track which blocks have overlaps
        press_times = []

        # Collect all press/release pairs using queue
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

        # Check if key is currently pressed (using dynamic calculation)
        active_keys_now = self._get_active_keys_at_time(self._snapshot_timestamp)

        if key.lower() in active_keys_now:
            press_time = active_keys_now[key.lower()]
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
            logger.debug(f"[TIMELINE] Key {key} is NOT currently pressed")

        # Calculate resolution based on actual number of blocks
        actual_resolution = VIEW_WINDOW_SECONDS / num_blocks
        
        # For each block, check if any press interval overlaps
        for i in range(num_blocks):
            block_start = view_start + (i * actual_resolution)
            block_end = block_start + actual_resolution

            block_active = False
            has_overlap = False
            
            # Check if this key is active in this block
            for press_start, press_end in press_times:
                if press_start < block_end and press_end > block_start:
                    block_active = True
                    break
            
            # Check for overlaps with other keys
            if block_active:
                for other_key, other_press_times in all_key_press_times.items():
                    if other_key.lower() == key.lower():
                        continue
                    for other_press_start, other_press_end in other_press_times:
                        # Check if this block overlaps with another key's press
                        block_overlaps_other = (
                            block_start < other_press_end and 
                            block_end > other_press_start
                        )
                        # Check if any of this key's presses overlap with the other key's press
                        key_overlaps_other = False
                        for press_start, press_end in press_times:
                            if (press_start < other_press_end and 
                                press_end > other_press_start):
                                key_overlaps_other = True
                                break
                        
                        if block_overlaps_other and key_overlaps_other:
                            has_overlap = True
                            break
                    if has_overlap:
                        break

            timeline.append('█' if block_active else ' ')
            timeline_overlaps.append(has_overlap)

        filled_count = timeline.count('█')
        logger.debug(f"[TIMELINE] key={key}, filled_blocks={filled_count}/{num_blocks}, press_times={press_times}")

        return ''.join(timeline), timeline_overlaps

    def render(self):
        """Render the piano roll using atomic snapshot."""
        from rich.text import Text

        self._create_snapshot()

        current_time = self._snapshot_timestamp
        # Apply view offset for navigation
        view_start = current_time - VIEW_WINDOW_SECONDS - self.view_offset
        view_end = current_time - self.view_offset

        logger.debug(f"[RENDER] Starting render at time={current_time:.3f}, view=[{view_start:.3f}, {view_end:.3f}], offset={self.view_offset:.3f}")

        active_keys = self._get_active_keys_in_window(view_start, view_end)
        
        # Calculate timeline width based on available space
        # Account for: label(12) + " | "(3) + timeline + " | "(3) + status(~15)
        # Total fixed width: ~33 chars, leave some margin
        available_width = max(self.size.width - 35, 40)  # minimum 40 blocks
        timeline_blocks = min(available_width, TIMELINE_BLOCK_WIDTH)
        separator_width = min(available_width + 10, 70)

        text = Text()
        text.append("DYNAMIC PIANO ROLL\n", style="bold #7aa2f7")
        text.append("=" * separator_width + "\n\n", style="dim")

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
            actual_resolution = VIEW_WINDOW_SECONDS / timeline_blocks
            text.append(f"Resolution: {actual_resolution*1000:.0f}ms/block ({timeline_blocks} blocks)", style="dim")
            if self.view_offset > 0:
                text.append(f" | Offset: -{self.view_offset:.1f}s", style="dim")

            logger.debug(f"[RENDER] No active keys, last_activity={last_activity}")
            return text

        sorted_keys = self._sort_keys_by_canonical_order(active_keys)
        logger.debug(f"[RENDER] Rendering {len(sorted_keys)} keys: {sorted_keys}")

        # Pre-calculate all key press times for overlap detection
        all_key_press_times = {}
        for key in sorted_keys:
            press_times = []
            pending_presses = deque()
            
            for event in self._events_snapshot:
                if event.key != key:
                    continue
                
                if event.event_type == 'press':
                    pending_presses.append(event.timestamp)
                elif event.event_type == 'release':
                    if pending_presses:
                        press_time = pending_presses.popleft()
                        press_times.append((press_time, event.timestamp))

            # Handle currently pressed key
            active_keys_now = self._get_active_keys_at_time(self._snapshot_timestamp)
            if key.lower() in active_keys_now:
                press_time = active_keys_now[key.lower()]
                already_matched = any(abs(ps - press_time) < 0.001 for ps, pe in press_times)
                if not already_matched:
                    if press_time >= view_start:
                        press_times.append((press_time, view_end))
                    else:
                        press_times.append((view_start, view_end))

            all_key_press_times[key] = press_times

        # Apply scroll offset
        display_keys = sorted_keys[self._scroll_offset:]
        max_label_length = 12
        
        for key in display_keys:
            label = key.upper()
            if len(label) > max_label_length:
                label = label[:max_label_length]

            text.append(f"{label.ljust(max_label_length)} | ", style="bold cyan")

            timeline, timeline_overlaps = self._calculate_key_timeline(
                key, view_start, view_end, 
                num_blocks=timeline_blocks,
                all_key_press_times=all_key_press_times
            )
            
            # Render timeline with overlap highlighting
            for i, char in enumerate(timeline):
                if timeline_overlaps[i] and char == '█':
                    text.append(char, style="bold red")
                else:
                    text.append(char, style="bold #7aa2f7")

            text.append(" | ", style="dim")

            # Check if key is currently pressed using dynamic calculation
            active_keys_now = self._get_active_keys_at_time(self._snapshot_timestamp)
            if key.lower() in active_keys_now:
                press_duration = current_time - active_keys_now[key.lower()]
                text.append(f"● {press_duration:.2f}s", style="bold green")
            else:
                text.append("○ released", style="dim")

            text.append("\n")

        text.append("\n", style="dim")
        text.append("-" * separator_width, style="dim")
        text.append(" Time (", style="dim")
        if self.view_offset > 0:
            text.append(f"{-VIEW_WINDOW_SECONDS - self.view_offset:.1f}s", style="bold #7aa2f7")
        else:
            text.append(f"{-VIEW_WINDOW_SECONDS:.0f}s", style="bold #7aa2f7")
        text.append(" → ", style="dim")
        if self.view_offset > 0:
            text.append(f"-{self.view_offset:.1f}s", style="bold #7aa2f7")
        else:
            text.append("now", style="bold #7aa2f7")
        text.append(")", style="dim")
        text.append("\n\n", style="dim")
        text.append(f"Active Keys: {len(sorted_keys)}  ", style="bold yellow")
        text.append(f"Total Events: {len(self._events_snapshot)}", style="dim")
        if self._scroll_offset > 0:
            text.append(f" | Scroll: +{self._scroll_offset}", style="dim")

        logger.debug(f"[RENDER] Complete, total events in snapshot: {len(self._events_snapshot)}")
        return text

    def clear(self):
        self.events.clear()
        self._events_snapshot = []
        self._snapshot_timestamp = 0.0
        self.view_offset = 0.0
        self._scroll_offset = 0
        self.refresh()
    
