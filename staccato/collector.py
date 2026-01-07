"""Keyboard event collector for Staccato."""

from pynput.keyboard import Key, KeyCode


class KeyboardCollector:
    """Manages background keyboard event collection.

    This class coordinates with the main app's background thread
    to capture keyboard events.
    """

    def __init__(self, app):
        """Initialize keyboard collector.

        Args:
            app: Reference to StaccatoApp instance
        """
        self.app = app
        self.is_running = False
        self.listener = None

    def start(self):
        """Start keyboard listener.

        This will trigger the app to start the background thread.
        """
        self.is_running = True
        # The app will start the actual listener thread
        # We just set the flag here

    def stop(self):
        """Stop keyboard listener."""
        self.is_running = False
        if self.listener:
            self.listener.stop()

    @staticmethod
    def get_key_name(key) -> str:
        """Extract readable key name from pynput key object.

        Args:
            key: pynput Key or KeyCode object

        Returns:
            Readable string representation of the key
        """
        if isinstance(key, KeyCode):
            return key.char or f"vk{key.vk}"
        elif isinstance(key, Key):
            return key.name.replace('_', ' ')
        return str(key)
