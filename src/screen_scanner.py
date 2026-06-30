"""
screen_scanner.py – Functions for screen reading, template matching,
and detection of game elements (units, roll triggers, boss HP bars).
"""

import time
from typing import List, Optional, Tuple

import cv2
import numpy as np
import pyautogui

from config import (
    SCAN_REGION,
    TEMPLATE_MATCH_THRESHOLD,
    SCREEN_CAPTURE_INTERVAL,
)
from utils import setup_logger

logger = setup_logger("screen_scanner")


# ── Template Cache ───────────────────────────────────────────────────────────
_template_cache: dict = {}


def load_template(name: str, path: str) -> Optional[np.ndarray]:
    """
    Load an image template from disk and cache it for reuse.

    Args:
        name: Identifier for the cached template.
        path: File path to the template image.

    Returns:
        Grayscale numpy array of the template, or None on failure.
    """
    if name in _template_cache:
        return _template_cache[name]

    try:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            _template_cache[name] = img
            logger.debug("Loaded template '%s' from %s", name, path)
        return img
    except Exception as exc:
        logger.error("Failed to load template '%s': %s", name, exc)
        return None


def capture_screen() -> np.ndarray:
    """
    Capture a screenshot and convert it to a numpy array in BGR format.

    Returns:
        Screenshot as a BGR numpy array.
    """
    if SCAN_REGION:
        x, y, w, h = SCAN_REGION
        screenshot = pyautogui.screenshot(region=(x, y, w, h))
    else:
        screenshot = pyautogui.screenshot()

    frame = np.array(screenshot)
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)


def find_template(
    screen: np.ndarray,
    template: np.ndarray,
    threshold: float = TEMPLATE_MATCH_THRESHOLD,
) -> Optional[Tuple[int, int, int, int]]:
    """
    Locate a template image within a screenshot using normalized
    cross-correlation.

    Args:
        screen:   BGR screenshot array.
        template: Grayscale template array.
        threshold: Minimum match confidence (0.0 – 1.0).

    Returns:
        (x, y, width, height) of the best match, or None if below threshold.
    """
    gray_screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(gray_screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        h, w = template.shape
        x, y = max_loc
        logger.debug("Template matched at (%d, %d) with confidence %.2f", x, y, max_val)
        return (x, y, w, h)

    logger.debug("Template not found (best confidence %.2f < %.2f)", max_val, threshold)
    return None


def detect_units(
    screen: np.ndarray, templates_dir: str
) -> List[Tuple[str, int, int, int, int]]:
    """
    Scan the screen for all known unit templates.

    Args:
        screen:        BGR screenshot array.
        templates_dir: Directory containing unit template images.

    Returns:
        List of (unit_name, x, y, w, h) for each detected unit.
    """
    from pathlib import Path

    detections: List[Tuple[str, int, int, int, int]] = []
    tpl_dir = Path(templates_dir)

    if not tpl_dir.is_dir():
        logger.warning("Templates directory not found: %s", templates_dir)
        return detections

    for tpl_file in tpl_dir.glob("*.png"):
        unit_name = tpl_file.stem
        template = load_template(unit_name, str(tpl_file))
        if template is None:
            continue
        match = find_template(screen, template)
        if match:
            x, y, w, h = match
            detections.append((unit_name, x, y, w, h))

    logger.info("Detected %d unit(s) on screen", len(detections))
    return detections


def detect_roll_trigger(screen: np.ndarray, template_path: str) -> bool:
    """
    Check whether the roll button / trigger is visible on screen.

    Args:
        screen:       BGR screenshot array.
        template_path: Path to the roll button template image.

    Returns:
        True if the roll trigger is detected, False otherwise.
    """
    template = load_template("roll_trigger", template_path)
    if template is None:
        return False
    return find_template(screen, template) is not None


def detect_boss_hp_bar(screen: np.ndarray) -> Optional[float]:
    """
    Attempt to read the boss HP bar and return the remaining HP fraction.

    This is a simplified demonstration. A production implementation would
    use color-based segmentation or a dedicated HP bar template.

    Args:
        screen: BGR screenshot array.

    Returns:
        Estimated HP fraction (0.0 – 1.0) or None if not detected.
    """
    # Define a rough region where the boss HP bar typically appears
    # (these values depend on game resolution and UI layout)
    hp_region = screen[50:80, 200:800]
    gray = cv2.cvtColor(hp_region, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Count non-zero pixels as a proxy for remaining HP
    hp_pixels = cv2.countNonZero(binary)
    total_pixels = binary.shape[0] * binary.shape[1]

    if total_pixels == 0:
        return None

    hp_fraction = hp_pixels / total_pixels
    hp_fraction = max(0.0, min(1.0, hp_fraction))
    logger.debug("Boss HP estimated at %.1f%%", hp_fraction * 100)
    return hp_fraction


def continuous_scan(
    callback, interval: float = SCREEN_CAPTURE_INTERVAL
) -> None:
    """
    Run a continuous screen capture loop, passing each frame to a callback.

    Args:
        callback: Function that accepts a numpy array (BGR frame).
        interval: Seconds between captures.
    """
    logger.info("Starting continuous screen scan (interval=%.1fs)", interval)
    try:
        while True:
            frame = capture_screen()
            callback(frame)
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Continuous scan stopped by user")
