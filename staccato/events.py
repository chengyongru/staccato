"""Core event data structures for Staccato."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from textual.message import Message


@dataclass
class KeyEvent:
    """Represents a single keyboard event.

    Attributes:
        key: Key character (e.g., 'w', 'a', 'space')
        event_type: 'press' or 'release'
        timestamp: perf_counter() timestamp for maximum precision
        vk_code: Virtual key code (Windows)
    """
    key: str
    event_type: str
    timestamp: float
    vk_code: Optional[int] = None


@dataclass
class KeyInteraction:
    """Represents an interaction between two keys.

    Attributes:
        key1: First key in the pair
        key2: Second key in the pair
        overlap_duration: Time duration of overlap in seconds
        overlap_percentage: Percentage of overlap relative to total press duration
    """
    key1: str
    key2: str
    overlap_duration: float
    overlap_percentage: float


@dataclass
class SessionMetrics:
    """Comprehensive session-level statistics for Signal Hygiene.

    Attributes:
        total_keypresses: Total number of key presses in session
        clean_keypresses: Key presses with zero overlap
        overlapping_keypresses: Key presses with any overlap detected
        hygiene_score: Composite score (0-100) of overall finger cleanliness
        adhesion_rate: Percentage of keypresses with overlap
        total_overlap_duration: Total time spent in adhesion (seconds)
        minor_adhesions: Count of overlaps < 50ms
        moderate_adhesions: Count of overlaps 50-100ms
        severe_adhesions: Count of overlaps > 100ms
        key_adhesion_map: Dictionary mapping key -> adhesion count
    """
    total_keypresses: int
    clean_keypresses: int
    overlapping_keypresses: int
    hygiene_score: float
    adhesion_rate: float
    total_overlap_duration: float
    minor_adhesions: int
    moderate_adhesions: int
    severe_adhesions: int
    key_adhesion_map: dict[str, int]


@dataclass
class KeySession:
    """Analyzable session of key events.

    Attributes:
        events: List of KeyEvent objects in chronological order
        start_time: perf_counter() timestamp when session started
        end_time: perf_counter() timestamp when session ended
        metadata: Additional session information
    """
    events: list[KeyEvent] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    metadata: dict = field(default_factory=dict)


class SessionEvent(Message):
    """Custom message for session events."""

    def __init__(self, session: KeySession) -> None:
        """Initialize session event.

        Args:
            session: The key session to pass with the event
        """
        self.session = session
        super().__init__()
