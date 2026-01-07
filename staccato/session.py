"""Session management for Staccato."""

import json
from pathlib import Path
from datetime import datetime
from staccato.events import KeySession, KeyEvent


class SessionManager:
    """Manages session save/load operations."""

    def __init__(self, save_dir: str = "sessions"):
        """Initialize session manager.

        Args:
            save_dir: Directory to save sessions (relative to current working dir)
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)

    def save_session(self, session: KeySession) -> Path:
        """Save session to JSON file.

        Args:
            session: KeySession to save

        Returns:
            Path to the saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_{timestamp}.json"
        filepath = self.save_dir / filename

        # Convert events to dict
        data = {
            "start_time": session.start_time,
            "end_time": session.end_time,
            "metadata": session.metadata,
            "events": [
                {
                    "key": e.key,
                    "event_type": e.event_type,
                    "timestamp": e.timestamp,
                    "vk_code": e.vk_code
                }
                for e in session.events
            ]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        return filepath

    def load_session(self, filepath: str) -> KeySession:
        """Load session from JSON file.

        Args:
            filepath: Path to session JSON file

        Returns:
            Loaded KeySession object
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Convert dicts to KeyEvent objects
        events = [
            KeyEvent(
                key=e["key"],
                event_type=e["event_type"],
                timestamp=e["timestamp"],
                vk_code=e.get("vk_code")
            )
            for e in data["events"]
        ]

        session = KeySession(
            events=events,
            start_time=data["start_time"],
            end_time=data["end_time"],
            metadata=data["metadata"]
        )

        return session

    def list_sessions(self) -> list[Path]:
        """List all saved session files.

        Returns:
            List of paths to session files
        """
        return sorted(self.save_dir.glob("session_*.json"))
