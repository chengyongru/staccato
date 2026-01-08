"""Timing analysis engine for Staccato."""

from dataclasses import dataclass
from typing import Optional
from staccato.events import KeyEvent, KeyInteraction


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

    def find_hotspot_overlaps(self, metrics: list[KeyMetrics], top_n: int = 3) -> list[KeyInteraction]:
        """Detect and rank overlapping key pairs by frequency and duration.

        Args:
            metrics: List of KeyMetrics to analyze
            top_n: Number of top hotspot pairs to return

        Returns:
            List of KeyInteraction objects sorted by overlap duration
        """
        from collections import defaultdict

        overlap_pairs = defaultdict(lambda: {'count': 0, 'total_duration': 0.0})

        for i, m1 in enumerate(metrics):
            for m2 in metrics[i+1:]:
                if (m1.release_time is not None and
                    m2.release_time is not None and
                    m1.press_time < m2.release_time and
                    m2.press_time < m1.release_time):

                    overlap_start = max(m1.press_time, m2.press_time)
                    overlap_end = min(m1.release_time, m2.release_time)
                    overlap_duration = overlap_end - overlap_start

                    if overlap_duration > 0:
                        pair_key = tuple(sorted([m1.key, m2.key]))
                        overlap_pairs[pair_key]['count'] += 1
                        overlap_pairs[pair_key]['total_duration'] += overlap_duration

        interactions = []
        for (key1, key2), data in overlap_pairs.items():
            total_duration = data['total_duration']
            count = data['count']
            avg_overlap_duration = total_duration / count if count > 0 else 0

            total_press_duration = sum(
                (m.release_time - m.press_time)
                for m in metrics
                if m.key in [key1, key2] and m.release_time is not None
            )

            overlap_percentage = (total_duration / total_press_duration * 100) if total_press_duration > 0 else 0

            interaction = KeyInteraction(
                key1=key1,
                key2=key2,
                overlap_duration=avg_overlap_duration,
                overlap_percentage=overlap_percentage
            )
            interactions.append(interaction)

        interactions.sort(key=lambda x: x.overlap_duration, reverse=True)
        return interactions[:top_n]

    def get_most_recent_pair_overlap(self, metrics: list[KeyMetrics]) -> Optional[KeyInteraction]:
        """Find the most recent overlapping key pair.

        Args:
            metrics: List of KeyMetrics to analyze

        Returns:
            KeyInteraction of the most recent overlap, or None if no overlaps found
        """
        recent_overlap = None
        latest_overlap_end = 0.0

        for i, m1 in enumerate(metrics):
            for m2 in metrics[i+1:]:
                if (m1.release_time is not None and
                    m2.release_time is not None and
                    m1.press_time < m2.release_time and
                    m2.press_time < m1.release_time):

                    overlap_start = max(m1.press_time, m2.press_time)
                    overlap_end = min(m1.release_time, m2.release_time)

                    if overlap_end > latest_overlap_end:
                        latest_overlap_end = overlap_end
                        overlap_duration = overlap_end - overlap_start

                        total_press_duration = (m1.release_time - m1.press_time) + (m2.release_time - m2.press_time)
                        overlap_percentage = (overlap_duration / total_press_duration * 100) if total_press_duration > 0 else 0

                        recent_overlap = KeyInteraction(
                            key1=m1.key,
                            key2=m2.key,
                            overlap_duration=overlap_duration,
                            overlap_percentage=overlap_percentage
                        )

        return recent_overlap
