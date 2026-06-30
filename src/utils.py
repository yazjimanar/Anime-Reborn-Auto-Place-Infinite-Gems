"""
utils.py – Helper utilities: logging setup, privilege checks, path resolution.
"""

import logging
import os
import sys
import ctypes
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "anime_reborn",
    level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True,
) -> logging.Logger:
    """
    Create and configure a logger with optional file and console handlers.

    Args:
        name:    Logger name.
        level:   Logging level string (e.g. "DEBUG", "INFO").
        log_file: Path to log file, or None to skip file logging.
        console: If True, add a StreamHandler for console output.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s │ %(message)s", datefmt="%H:%M:%S"
    )

    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


def is_admin() -> bool:
    """
    Check whether the current process has administrator / root privileges.

    Returns:
        True if running with elevated privileges, False otherwise.
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        # Fallback for non-Windows platforms
        return os.geteuid() == 0 if hasattr(os, "geteuid") else False


def require_admin() -> None:
    """
    Exit with a warning if the script is not running as administrator.
    Screen capture on Windows may require elevated privileges for certain windows.
    """
    if not is_admin():
        sys.exit(
            "[WARNING] This script should be run as Administrator for reliable "
            "screen capture. Right-click → Run as administrator, then try again."
        )


def resolve_path(relative: str) -> Path:
    """
    Resolve a path relative to the project root (parent of src/).

    Args:
        relative: Path string relative to the project root.

    Returns:
        Absolute Path object.
    """
    project_root = Path(__file__).resolve().parent.parent
    return (project_root / relative).resolve()
