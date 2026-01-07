"""Timing analysis engine for Staccato."""

from dataclasses import dataclass
from typing import Optional
from staccato.events import KeyEvent


@dataclass
class KeyMetrics:
    """Metrics for a single key press.

    Attributes:
        key: The key character
        press_time: Timestamp when key was pressed
        release_time: Timestamp when key was released (None if still pressed)
        duration: Time between press and release in seconds (None if still pressed)
        overlap_with: Key that this press overlapped with
        overlap_duration: Duration of overlap in seconds
    """
    key: str
    press_time: float
    release_time: Optional[float]
    duration: Optional[float]
    overlap_with: Optional[str] = None
    overlap_duration: float = 0.0


class TimingAnalyzer:
    """Analyzes key timing patterns."""

    def analyze_session(self, events: list[KeyEvent]) -> list[KeyMetrics]:
        """Convert raw events to analyzed metrics.

        Args:
            events: List of KeyEvent objects in chronological order

        Returns:
            List of KeyMetrics with duration information
        """
        metrics = []
        active_presses = {}  # key -> press time

        for event in events:
            if event.event_type == 'press':
                # Track when key was pressed
                active_presses[event.key] = event.timestamp

            elif event.event_type == 'release':
                if event.key in active_presses:
                    press_time = active_presses[event.key]
                    duration = event.timestamp - press_time

                    metric = KeyMetrics(
                        key=event.key,
                        press_time=press_time,
                        release_time=event.timestamp,
                        duration=duration
                    )
                    metrics.append(metric)
                    del active_presses[event.key]

        return metrics

    def detect_overlaps(self, metrics: list[KeyMetrics]) -> dict[str, float]:
        """Detect overlapping key presses.

        Args:
            metrics: List of KeyMetrics to analyze

        Returns:
            Dictionary mapping "key1+key2" pairs to overlap duration in seconds
        """
        overlaps = {}

        for i, m1 in enumerate(metrics):
            for m2 in metrics[i+1:]:
                # Check if key presses overlap in time
                if (m1.release_time is not None and
                    m2.release_time is not None and
                    m1.press_time < m2.release_time and
                    m2.press_time < m1.release_time):

                    overlap_start = max(m1.press_time, m2.press_time)
                    overlap_end = min(m1.release_time, m2.release_time)
                    overlap_duration = overlap_end - overlap_start

                    if overlap_duration > 0:
                        pair = f"{m1.key}+{m2.key}"
                        overlaps[pair] = overlap_duration

        return overlaps

    def calculate_kps(self, events: list[KeyEvent], window: float = 1.0) -> float:
        """Calculate keys per second.

        Args:
            events: List of KeyEvent objects
            window: Time window in seconds to look back

        Returns:
            Keys per second in the time window
        """
        if not events:
            return 0.0

        latest_time = events[-1].timestamp
        recent_presses = [
            e for e in events
            if e.event_type == 'press' and latest_time - e.timestamp <= window
        ]

        return len(recent_presses) / window
