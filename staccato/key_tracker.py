"""Key state tracker for Staccato - centralizes key press/release state management."""

from staccato.events import KeyEvent
from staccato.logger import get_logger

logger = get_logger("KEY_TRACKER")


class KeyStateTracker:
    """Centralized tracker for key press/release state.
    
    This module manages the active keys state independently and provides
    a unified event stream for all listeners. Listeners register callbacks
    to receive key events with proper state management.
    """

    def __init__(self):
        self.active_keys = {}
        self.listeners = []

    def add_listener(self, callback):
        """Register a callback to receive key events.
        
        Args:
            callback: Function that accepts (event, active_keys) parameters
        """
        if callback not in self.listeners:
            self.listeners.append(callback)
            logger.debug(f"[KEY_TRACKER] Added listener, total={len(self.listeners)}")

    def remove_listener(self, callback):
        """Unregister a callback.
        
        Args:
            callback: Function to remove from listeners
        """
        if callback in self.listeners:
            self.listeners.remove(callback)
            logger.debug(f"[KEY_TRACKER] Removed listener, remaining={len(self.listeners)}")

    def process_event(self, event: KeyEvent):
        """Process a key event and update state.

        Args:
            event: KeyEvent to process
        """
        key = event.key.lower()

        if event.event_type == 'press':
            if key in self.active_keys:
                logger.debug(f"[KEY_TRACKER] Ignoring repeat press for {event.key}")
                return False

            self.active_keys[key] = event.timestamp
            logger.debug(f"[KEY_TRACKER] PRESS {event.key}, active_keys={list(self.active_keys.keys())}")
            
            # Notify listeners with current state
            self._notify_listeners(event, dict(self.active_keys))

        elif event.event_type == 'release':
            # For release events, create a snapshot that includes the key being released
            # This allows listeners to calculate duration before we remove it
            if key in self.active_keys:
                # Key exists, create snapshot with the key
                snapshot = dict(self.active_keys)
                logger.debug(f"[KEY_TRACKER] RELEASE {event.key} (was in active_keys), active_keys={list(self.active_keys.keys())}")
                # Notify listeners with snapshot
                self._notify_listeners(event, snapshot)
                # Now remove the key
                del self.active_keys[key]
            else:
                # Key doesn't exist (e.g., window focus change), notify with empty snapshot
                logger.debug(f"[KEY_TRACKER] Release {event.key} not in active_keys, forwarding with empty snapshot")
                self._notify_listeners(event, {})
        
        return True

    def _notify_listeners(self, event: KeyEvent, active_keys_snapshot: dict):
        """Notify all registered listeners of the event.
        
        Args:
            event: KeyEvent to notify listeners about
            active_keys_snapshot: Snapshot of active keys at the time of event
        """
        for listener in self.listeners:
            try:
                listener(event, active_keys_snapshot)
            except Exception as e:
                logger.error(f"[KEY_TRACKER] Error in listener: {e}")

    def get_active_keys(self):
        """Get a snapshot of currently active keys.
        
        Returns:
            dict: Copy of active_keys mapping
        """
        return dict(self.active_keys)

    def clear(self):
        """Clear all state."""
        self.active_keys.clear()
        logger.debug(f"[KEY_TRACKER] Cleared all state")
