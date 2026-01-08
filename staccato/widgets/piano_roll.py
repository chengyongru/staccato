"""Dynamic piano roll widget for Staccato v3.0."""

from textual.widget import Widget
from collections import deque
from staccato.events import KeyEvent
from staccato.constants import CANONICAL_KEY_ORDER, VIEW_WINDOW_SECONDS, VIEW_RESOLUTION, TIMELINE_BLOCK_WIDTH, TIME_ALIGNMENT_INTERVAL
from rich.text import Text
import time
import sys
import hashlib

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

        # Track timestamp of last event for reference
        self._last_event_time = 0.0  # Timestamp of last event

        # Navigation state
        self.view_offset = 0.0  # Time offset for navigation (in seconds)
        self._scroll_offset = 0  # Vertical scroll offset for key list

        # Rendering optimization: time alignment to reduce flicker
        self._last_render_content_hash = None
        # Use time alignment interval from constants to match block duration exactly
        # This prevents block boundaries from shifting relative to event timestamps
        self._time_alignment_interval = TIME_ALIGNMENT_INTERVAL

        # Double buffering: cache last rendered content for diffing
        self._last_rendered_text = None

    def add_event(self, event: KeyEvent, active_keys=None):
        logger.debug(f"[ADD_EVENT] key={event.key}, type={event.event_type}, timestamp={event.timestamp:.3f}")

        self.events.append(event)
        # Update last event time when new event arrives
        if event.timestamp > self._last_event_time:
            self._last_event_time = event.timestamp

    def _create_snapshot(self):
        """Create an atomic snapshot of current state for rendering."""
        old_snapshot_len = len(self._events_snapshot)
        self._events_snapshot = list(self.events)
        events_changed = len(self._events_snapshot) != old_snapshot_len

        # Update last event time if we have events
        if self._events_snapshot:
            latest_event_time = self._events_snapshot[-1].timestamp
            if latest_event_time > self._last_event_time:
                self._last_event_time = latest_event_time

        # Capture current time once per render for frame consistency
        current_time = time.perf_counter()

        # FIX 1: Time Quantization - Lock time to fixed grid (20FPS = 50ms intervals)
        # This prevents microsecond-level jitter and ensures consistent step size
        aligned_time = (current_time // self._time_alignment_interval) * self._time_alignment_interval

        # Only update snapshot time when aligned time advances or events change
        # This creates smooth, predictable frame updates instead of continuous jitter
        if aligned_time > self._snapshot_timestamp or events_changed:
            self._snapshot_timestamp = aligned_time

        # If no events yet, initialize last event time
        if self._last_event_time == 0.0 and self._events_snapshot:
            self._last_event_time = self._events_snapshot[-1].timestamp

        logger.debug(f"[SNAPSHOT] Created at render_time={self._snapshot_timestamp:.3f}, "
                     f"last_event_time={self._last_event_time:.3f}, "
                     f"events={len(self._events_snapshot)}, changed={events_changed}")

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

    def _get_key_press_times(self, key, view_start, view_end) -> list[tuple[float, float]]:
        """Extract and match press/release pairs for a key.

        Args:
            key: Key name to extract press times for
            view_start: Start of view window
            view_end: End of view window

        Returns:
            list: List of (press_start, press_end) tuples
        """
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

        return press_times

    def _calculate_key_timeline(self, key, view_start, view_end, num_blocks=None, all_key_press_times=None):
        """Calculate timeline with DIRECTIONAL geometric blocks for seamless visual flow.

        KEY INSIGHT: Blocks must be directionally aware to eliminate gaps.
        - HEAD (note starts here): Use RIGHT-aligned blocks via reverse color masking
        - TAIL (note ends here): Use LEFT-aligned blocks (normal)
        - BODY (full coverage): Use solid block
        - ISLAND (note entirely within block): Use LEFT-aligned blocks

        This creates "welded" appearance like solid metal bars, not disconnected segments.

        Args:
            key: Key name
            view_start: Start of view window
            view_end: End of view window
            num_blocks: Number of timeline blocks (auto-calculated if None)
            all_key_press_times: Dict mapping key -> list of (press_start, press_end) tuples for overlap detection

        Returns:
            tuple: (timeline_chars, timeline_types)
                - timeline_chars: list of characters
                - timeline_types: list of 'head', 'tail', 'body', 'island', or 'empty'
        """
        if num_blocks is None:
            num_blocks = TIMELINE_BLOCK_WIDTH

        if all_key_press_times is None:
            all_key_press_times = {}

        timeline_chars = []
        timeline_types = []

        logger.debug(f"[TIMELINE] key={key}, view_start={view_start:.3f}, view_end={view_end:.3f}")

        # Use helper method to get press times
        press_times = self._get_key_press_times(key, view_start, view_end)

        # Calculate duration of each block
        block_duration = (view_end - view_start) / num_blocks

        # GEOMETRIC BLOCKS: Left-to-right fill (0/8 to 8/8)
        BLOCK_CHARS = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]

        for i in range(num_blocks):
            block_start = view_start + (i * block_duration)
            block_end = block_start + block_duration

            # Find the active interval in this block
            active_interval = None
            for press_start, press_end in press_times:
                overlap_start = max(press_start, block_start)
                overlap_end = min(press_end, block_end)
                if overlap_start < overlap_end:
                    active_interval = (overlap_start, overlap_end)
                    break  # Use first/primary interval

            if not active_interval:
                timeline_chars.append(' ')
                timeline_types.append('empty')
                continue

            interval_start, interval_end = active_interval

            # Determine block type (HEAD/TAIL/BODY/ISLAND)
            starts_in_block = interval_start > block_start
            ends_in_block = interval_end < block_end
            spans_full_block = interval_start <= block_start and interval_end >= block_end

            if spans_full_block:
                block_type = 'body'
                char = '█'
                fill_ratio = 1.0
            elif starts_in_block and not ends_in_block:
                # HEAD: Note starts here, extends to the right
                block_type = 'head'
                fill_ratio = (interval_end - interval_start) / block_duration
            elif not starts_in_block and ends_in_block:
                # TAIL: Note comes from left, ends here
                block_type = 'tail'
                fill_ratio = (interval_end - interval_start) / block_duration
            else:
                # ISLAND: Note entirely within this block
                block_type = 'island'
                fill_ratio = (interval_end - interval_start) / block_duration

            fill_ratio = max(0.0, min(1.0, fill_ratio))

            # Calculate character based on block type
            if block_type == 'body':
                char = '█'
            elif block_type == 'head':
                # HEAD: Use RIGHT-aligned via reverse masking
                # Calculate empty portion on the LEFT
                empty_ratio = 1.0 - fill_ratio
                char_idx = int(empty_ratio * 8)
                char_idx = max(0, min(char_idx, len(BLOCK_CHARS) - 1))
                char = BLOCK_CHARS[char_idx]
            else:
                # TAIL and ISLAND: Use LEFT-aligned (normal)
                char_idx = int(fill_ratio * 8)
                if char_idx == 0 and fill_ratio > 0:
                    char_idx = 1  # Minimum visibility
                char_idx = max(0, min(char_idx, len(BLOCK_CHARS) - 1))
                char = BLOCK_CHARS[char_idx]

            timeline_chars.append(char)
            timeline_types.append(block_type)

            # DEBUG: Log directional blocks
            if block_type != 'body':
                logger.debug(f"[DIRECTIONAL] block {i}, type={block_type}, ratio={fill_ratio:.3f}, "
                           f"char='{char}', block=[{block_start:.3f}, {block_end:.3f}]")

        # Calculate approximate fill percentage for logging
        fill_ratio = sum([1 if c != ' ' else 0 for c in timeline_chars]) / num_blocks
        logger.debug(f"[TIMELINE] key={key}, fill_ratio={fill_ratio:.1%}, press_times={press_times}")

        return timeline_chars, timeline_types

    def render(self):
        """Render the piano roll using atomic snapshot."""
        self._create_snapshot()

        # Use snapshot timestamp for view window to ensure smooth time-based scrolling
        # The snapshot timestamp is captured once per render, ensuring consistency within a frame
        # This allows the view window to scroll smoothly with time, even when no new events occur
        render_time = self._snapshot_timestamp  # For checking current key states and view window
        
        # Apply view offset for navigation
        # View window scrolls with time, using snapshot timestamp for frame consistency
        view_start = render_time - VIEW_WINDOW_SECONDS - self.view_offset
        view_end = render_time - self.view_offset

        logger.debug(f"[RENDER] render_time={render_time:.3f}, "
                     f"view=[{view_start:.3f}, {view_end:.3f}], offset={self.view_offset:.3f}")

        # Double buffering + Diffing: Calculate content signature for change detection
        # FIX 2: Match hash precision to time alignment interval (50ms = 0.05s = 2 decimal places)
        # This prevents cache misses due to precision mismatch
        # Using quantized time ensures hash changes predictably with frame updates
        active_keys_set = self._get_active_keys_in_window(view_start, view_end)
        active_keys_sorted = sorted(active_keys_set)
        content_key = (
            f"{len(self._events_snapshot)}|"
            f"{view_start:.2f}|{view_end:.2f}|"
            f"{self._scroll_offset}|{self.view_offset}|"
            f"{active_keys_sorted}"
        )
        content_hash = hashlib.md5(content_key.encode()).hexdigest()

        # Diffing: Only skip render if content truly unchanged
        # With time quantization, hash now changes predictably at 50ms boundaries
        # This prevents cache misses due to microsecond-level time jitter
        if content_hash == self._last_render_content_hash and self._last_rendered_text is not None:
            logger.debug(f"[RENDER] Content unchanged, returning cached result")
            return self._last_rendered_text

        # Content has changed (time advanced or events changed) - proceed with full render
        # Textual's double buffering will handle the atomic swap
        self._last_render_content_hash = content_hash

        # Reuse the already-computed active keys for rendering
        active_keys = active_keys_set
        
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
                last_activity = render_time - self._events_snapshot[-1].timestamp

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
            all_key_press_times[key] = self._get_key_press_times(key, view_start, view_end)

        # Apply scroll offset
        display_keys = sorted_keys[self._scroll_offset:]
        max_label_length = 12
        
        for key in display_keys:
            label = key.upper()
            if len(label) > max_label_length:
                label = label[:max_label_length]

            text.append(f"{label.ljust(max_label_length)} | ", style="bold cyan")

            timeline_chars, timeline_types = self._calculate_key_timeline(
                key, view_start, view_end,
                num_blocks=timeline_blocks,
                all_key_press_times=all_key_press_times
            )

            # Render timeline with DIRECTIONAL color logic
            # CRITICAL: HEAD blocks use reverse color masking for right-alignment
            for i, (char, block_type) in enumerate(zip(timeline_chars, timeline_types)):
                if block_type == 'empty':
                    # Empty blocks
                    text.append(char, style="dim")

                elif block_type == 'head':
                    # HEAD: Reverse color masking for RIGHT-alignment
                    # Foreground = canvas color (#1a202c), Background = note color (#7aa2f7)
                    # This makes the LEFT part of character "invisible", revealing RIGHT-aligned color
                    text.append(char, style="#1a202c on #7aa2f7")

                elif char == '█':
                    # Full body blocks: bright blue
                    text.append(char, style="bold #7aa2f7")

                elif char in ('▉', '▊', '▋'):
                    # Mostly filled: medium blue
                    text.append(char, style="#7aa2f7")

                elif char in ('▌', '▍'):
                    # Half filled: dim blue
                    text.append(char, style="dim #7aa2f7")

                elif char in ('▎', '▏'):
                    # Lightly filled: very dim blue
                    text.append(char, style="dim #5d7bb8")

                else:
                    # Fallback
                    text.append(char, style="dim")

            text.append(" | ", style="dim")

            # Check if key is currently pressed using dynamic calculation
            # Use render_time (actual current time) for accurate duration display
            active_keys_now = self._get_active_keys_at_time(render_time)
            if key.lower() in active_keys_now:
                press_duration = render_time - active_keys_now[key.lower()]
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
        
        # Cache the rendered result for diffing (double buffering)
        self._last_rendered_text = text
        return text

    def clear(self):
        self.events.clear()
        self._events_snapshot = []
        self._snapshot_timestamp = 0.0
        self._last_event_time = 0.0
        self.view_offset = 0.0
        self._scroll_offset = 0
        self._last_rendered_text = None
        self._last_render_content_hash = None
        self.refresh()
    
