"""Keyboard event collector for Staccato."""

import keyboard
import threading
from staccato.events import KeyEvent
import time


class KeyboardCollector:
    """Manages background keyboard event collection.

    Uses the keyboard library for better Windows compatibility.
    """

    def __init__(self, app):
        """Initialize keyboard collector.

        Args:
            app: Reference to StaccatoApp instance
        """
        self.app = app
        self.is_running = False
        self._thread = None

    def start(self):
        """Start keyboard listener in background thread."""
        self.is_running = True
        self._thread = threading.Thread(
            target=self._run_keyboard_listener,
            name="keyboard_listener",
            daemon=True
        )
        self._thread.start()

    def stop(self):
        """Stop keyboard listener."""
        self.is_running = False
        keyboard.unhook_all()

    def _run_keyboard_listener(self):
        """Run keyboard listener using keyboard library."""
        def on_event(event):
            if not self.is_running:
                return False  # Unhook

            try:
                key_name = self.get_key_name(event.name)
                timestamp = time.perf_counter()

                event_type = 'press' if event.event_type == 'down' else 'release'

                key_event = KeyEvent(
                    key=key_name,
                    event_type=event_type,
                    timestamp=timestamp
                )

                try:
                    self.app.event_queue.put_nowait(key_event)
                except:
                    pass  # Queue full, ignore

            except Exception:
                pass  # Ignore errors

            return True  # Continue listening

        # Hook all keyboard events
        keyboard.hook(on_event)

        # Keep the thread alive
        while self.is_running:
            threading.sleep(0.1)

    @staticmethod
    def get_key_name(name: str) -> str:
        """Extract readable key name from keyboard library event.

        Args:
            name: Key name from keyboard library

        Returns:
            Readable string representation of the key
        """
        if name is None:
            return "unknown"

        # Special key mappings for consistency
        special_mappings = {
            'space': 'space',
            'enter': 'enter',
            'backspace': 'backspace',
            'tab': 'tab',
            'shift': 'shift',
            'shift_l': 'left shift',
            'shift_r': 'right shift',
            'ctrl': 'ctrl',
            'ctrl_l': 'left ctrl',
            'ctrl_r': 'right ctrl',
            'alt': 'alt',
            'alt_l': 'left alt',
            'alt_r': 'right alt',
            'caps_lock': 'caps lock',
            'esc': 'esc',
            'up': 'up',
            'down': 'down',
            'left': 'left',
            'right': 'right',
            'home': 'home',
            'end': 'end',
            'page_up': 'page up',
            'page_down': 'page down',
            'delete': 'delete',
            'insert': 'insert',
            'num_lock': 'num lock',
            'print_screen': 'print screen',
            'pause': 'pause',
            'menu': 'menu',
            'f1': 'f1',
            'f2': 'f2',
            'f3': 'f3',
            'f4': 'f4',
            'f5': 'f5',
            'f6': 'f6',
            'f7': 'f7',
            'f8': 'f8',
            'f9': 'f9',
            'f10': 'f10',
            'f11': 'f11',
            'f12': 'f12',
        }

        name_lower = name.lower()
        if name_lower in special_mappings:
            return special_mappings[name_lower]

        # Return single character keys as-is
        if len(name) == 1:
            return name.lower()

        # For unknown keys, return as-is
        return name
