"""Unified logging configuration for Staccato."""

from pathlib import Path
from loguru import logger
import tomllib

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

# Configure unified logger - only configure once
_logger_configured = False

def _load_debug_config() -> bool:
    """Load debug configuration from pyproject.toml.

    Returns:
        True if debug mode is enabled, False otherwise
    """
    try:
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                config = tomllib.load(f)
                return config.get("tool", {}).get("staccato", {}).get("logging", {}).get("debug", False)
    except (OSError, tomllib.TOMLDecodeError) as e:
        # Silently fall back to False - debug config is optional
        pass
    return False

def configure_logger():
    """Configure unified logger for all modules."""
    global _logger_configured
    
    if _logger_configured:
        return
    
    # Load debug configuration
    debug_mode = _load_debug_config()
    log_level = "DEBUG" if debug_mode else "WARNING"
    
    # Remove default handler
    logger.remove()
    
    # Add console handler with appropriate level
    logger.add(
        lambda msg: print(msg, end=""),
        level=log_level,
        format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>[{extra[module]: <12}]</cyan> | <level>{message}</level>",
        colorize=True,
    )
    
    # Add unified log file with module field
    logger.add(
        str(LOG_FILE),
        rotation="10 MB",
        retention="1 day",
        level="DEBUG",  # Always log DEBUG to file
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

