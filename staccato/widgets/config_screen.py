"""Configuration screen widget for Staccato."""

from textual.widget import Widget
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Input, Button
from staccato.constants import VIEW_WINDOW_SECONDS, TIMELINE_BLOCK_WIDTH
from staccato.logger import get_logger

logger = get_logger("CONFIG")


class ConfigScreen(Widget):
    """Configuration screen for Staccato."""

    DEFAULT_CSS = """
    ConfigScreen {
        background: #0a0e14;
        layout: vertical;
        padding: 1;
    }

    ConfigScreen > Vertical {
        background: #1a202c;
        border: solid #7aa2f7;
        padding: 1;
        margin: 1;
    }

    ConfigScreen > Vertical > Horizontal {
        margin: 1 0;
        height: 3;
    }

    ConfigScreen > Vertical > Horizontal > Static {
        width: 20;
        color: #c0caf5;
    }

    ConfigScreen > Vertical > Horizontal > Input {
        width: 1fr;
        background: #24283b;
        border: solid #414868;
        color: #c0caf5;
    }

    ConfigScreen > Vertical > Horizontal > Button {
        margin: 0 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.view_window_seconds = VIEW_WINDOW_SECONDS
        self.timeline_block_width = TIMELINE_BLOCK_WIDTH

    def compose(self):
        """Compose the configuration screen."""
        with Vertical(id="config-container"):
            yield Static("Configuration", classes="title")
            
            with Horizontal():
                yield Static("View Window (s):")
                yield Input(
                    str(self.view_window_seconds),
                    id="input-view-window",
                    type="number"
                )
            
            with Horizontal():
                yield Static("Timeline Blocks:")
                yield Input(
                    str(self.timeline_block_width),
                    id="input-timeline-blocks",
                    type="number"
                )
            
            with Horizontal():
                yield Button("Save", id="btn-save-config", variant="primary")
                yield Button("Cancel", id="btn-cancel-config")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        if event.input.id == "input-view-window":
            try:
                self.view_window_seconds = float(event.value)
            except ValueError:
                pass
        elif event.input.id == "input-timeline-blocks":
            try:
                self.timeline_block_width = int(event.value)
            except ValueError:
                pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-save-config":
            self.save_config()
        elif event.button.id == "btn-cancel-config":
            self.dismiss()

    def save_config(self):
        """Save configuration and dismiss."""
        # Update constants (in a real implementation, these would be saved to a file)
        from staccato import constants
        constants.VIEW_WINDOW_SECONDS = self.view_window_seconds
        constants.TIMELINE_BLOCK_WIDTH = self.timeline_block_width
        
        logger.info(f"Configuration saved: window={self.view_window_seconds}s, blocks={self.timeline_block_width}")
        self.dismiss()

    def dismiss(self):
        """Dismiss the configuration screen."""
        if hasattr(self, 'app') and self.app:
            self.app.set_mode('normal')
        if self.parent:
            self.remove()
