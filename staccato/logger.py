"""Unified logging configuration for Staccato."""

from pathlib import Path
from loguru import logger

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

# Configure unified logger - only configure once
_logger_configured = False

def configure_logger():
    """Configure unified logger for all modules."""
    global _logger_configured
    
    if _logger_configured:
        return
    
    # Remove default handler
    logger.remove()
    
    # Add unified log file with module field
    logger.add(
        str(LOG_FILE),
        rotation="10 MB",
        retention="1 day",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | [{extra[module]: <12}] | {message}",
        encoding="utf-8",
    )
    
    _logger_configured = True

def get_logger(module_name: str):
    """Get logger instance bound to a specific module.
    
    Args:
        module_name: Name of the module (e.g., "APP", "COLLECTOR", "EVENT_LOG")
    
    Returns:
        Logger instance bound to the module name
    """
    configure_logger()
    return logger.bind(module=module_name)

