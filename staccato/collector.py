"""Keyboard event collector for Staccato."""

import keyboard
import threading
from staccato.events import KeyEvent
import time
import traceback

from staccato.logger import get_logger

logger = get_logger("COLLECTOR")


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
        logger.info("[COLLECTOR] Initialized")

    def start(self):
        """Start keyboard listener in background thread."""
        logger.info("[COLLECTOR] Starting...")
        self.is_running = True
        self._thread = threading.Thread(
            target=self._run_keyboard_listener,
            name="keyboard_listener",
            daemon=True
        )
        self._thread.start()
        logger.info(f"[COLLECTOR] Thread started, is_running={self.is_running}")

    def stop(self):
        """Stop keyboard listener."""
        logger.info("[COLLECTOR] Stopping...")
        self.is_running = False
        keyboard.unhook_all()
        logger.info("[COLLECTOR] Stopped")

    def _run_keyboard_listener(self):
        """Run keyboard listener using keyboard library."""
        logger.info("[COLLECTOR] Listener thread started")

        def on_event(event):
            if not self.is_running:
                logger.warning("[COLLECTOR] Listener stopped, ignoring event")
                return False  # Unhook

            try:
                logger.debug(f"[COLLECTOR] Raw event: name={event.name}, type={event.event_type}")
                key_name = self.get_key_name(event.name)
                timestamp = time.perf_counter()
                event_type = 'press' if event.event_type == 'down' else 'release'

                key_event = KeyEvent(
                    key=key_name,
                    event_type=event_type,
                    timestamp=timestamp
                )
                logger.debug(f"[COLLECTOR] Created KeyEvent: key={key_name}, type={event_type}")

                try:
                    self.app.event_queue.put_nowait(key_event)
                    logger.debug(f"[COLLECTOR] Queued event, queue_size estimated")
                except Exception as e:
                    logger.error(f"[COLLECTOR] Queue put failed: {e}")

            except Exception as e:
                logger.error(f"[COLLECTOR] Event processing failed: {e}")
                logger.error(traceback.format_exc())

            return True  # Continue listening

        logger.info("[COLLECTOR] Hooking keyboard events...")
        keyboard.hook(on_event)
        logger.info("[COLLECTOR] Keyboard hook registered")

        # Keep the thread alive
        while self.is_running:
            threading.sleep(0.1)

        logger.info("[COLLECTOR] Listener thread exiting")

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
