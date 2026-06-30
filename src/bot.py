"""
bot.py – Core bot class handling auto-placement, auto-roll,
auto-quest, and auto-boss logic.
"""

import time
from typing import List, Optional, Callable

import pyautogui

from config import (
    GRID_COLS,
    GRID_ROWS,
    PREFERRED_SLOTS,
    ROLL_DELAY,
    QUEST_ACCEPT_DELAY,
    BOSS_ENGAGE_DELAY,
    PLACE_UNIT_DELAY,
    MAX_ROLLS_PER_SESSION,
    BOSS_RETRY_COUNT,
    BOSS_HEALTH_THRESHOLD,
    ROLL_PATTERN,
)
from screen_scanner import (
    capture_screen,
    detect_units,
    detect_roll_trigger,
    detect_boss_hp_bar,
)
from utils import setup_logger, resolve_path

logger = setup_logger("bot")

# Safety: fail-safe to move mouse to a corner on abort
pyautogui.FAILSAFE = True


class AnimeRebornBot:
    """
    High-level bot that orchestrates auto-placement, auto-roll,
    auto-quest, and auto-boss behaviours.
    """

    def __init__(self) -> None:
        self._running = False
        self._paused = False
        self._rolls_done = 0
        self.templates_dir = str(resolve_path("templates"))
        self.roll_trigger_path = str(resolve_path("templates/roll_trigger.png"))

    # ── State Control ────────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start the bot's main loop."""
        if self._running:
            logger.warning("Bot is already running")
            return
        self._running = True
        self._paused = False
        self._rolls_done = 0
        logger.info("Bot started")

    def stop(self) -> None:
        """Stop the bot gracefully."""
        self._running = False
        self._paused = False
        logger.info("Bot stopped")

    def pause(self) -> None:
        """Toggle pause state."""
        self._paused = not self._paused
        state = "paused" if self._paused else "resumed"
        logger.info("Bot %s", state)

    def _wait_if_paused(self) -> None:
        """Block while the bot is paused."""
        while self._paused and self._running:
            time.sleep(0.1)

    # ── Coordinate Helpers ───────────────────────────────────────────────

    def _slot_to_screen(self, slot_index: int) -> tuple:
        """
        Convert a grid slot index to approximate screen coordinates.

        Args:
            slot_index: Zero-based index in row-major order.

        Returns:
            (x, y) screen coordinates for the slot centre.
        """
        row = slot_index // GRID_COLS
        col = slot_index % GRID_COLS
        # These offsets depend on the game window size and grid layout.
        # Values below assume a 1920×1080 display with the grid centred.
        grid_origin_x, grid_origin_y = 640, 350
        cell_w, cell_h = 110, 100
        x = grid_origin_x + col * cell_w + cell_w // 2
        y = grid_origin_y + row * cell_h + cell_h // 2
        return (x, y)

    # ── Auto Place ───────────────────────────────────────────────────────

    def auto_place(self) -> int:
        """
        Scan the screen for detected units and place them in preferred
        grid slots.

        Returns:
            Number of units placed.
        """
        screen = capture_screen()
        units = detect_units(screen, self.templates_dir)
        placed = 0

        for i, (unit_name, ux, uy, uw, uh) in enumerate(units):
            if i >= len(PREFERRED_SLOTS):
                logger.info("No more preferred slots available")
                break

            target_x, target_y = self._slot_to_screen(PREFERRED_SLOTS[i])
            # Click on the unit to pick it up
            click_x = ux + uw // 2
            click_y = uy + uh // 2
            pyautogui.click(click_x, click_y)
            time.sleep(0.3)
            # Click on the target slot to place it
            pyautogui.click(target_x, target_y)
            placed += 1
            logger.info("Placed '%s' at slot %d (%d, %d)", unit_name, PREFERRED_SLOTS[i], target_x, target_y)
            time.sleep(PLACE_UNIT_DELAY)

        logger.info("Auto-place complete: %d unit(s) placed", placed)
        return placed

    # ── Auto Roll ────────────────────────────────────────────────────────

    def auto_roll(self, count: Optional[int] = None) -> int:
        """
        Perform automated rolls, clicking the roll trigger when detected.

        Args:
            count: Maximum rolls to perform, or None for session cap.

        Returns:
            Number of rolls performed.
        """
        max_rolls = count if count is not None else MAX_ROLLS_PER_SESSION
        performed = 0

        logger.info("Starting auto-roll (max=%d, pattern=%s)", max_rolls, ROLL_PATTERN)

        while performed < max_rolls and self._running:
            self._wait_if_paused()
            screen = capture_screen()

            if detect_roll_trigger(screen, self.roll_trigger_path):
                # Click the centre of the matched region
                pyautogui.click()
                performed += 1
                self._rolls_done += 1
                logger.info("Roll %d/%d executed", performed, max_rolls)
                time.sleep(ROLL_DELAY)
            else:
                time.sleep(0.5)

        logger.info("Auto-roll finished: %d roll(s)", performed)
        return performed

    # ── Auto Quest ───────────────────────────────────────────────────────

    def auto_quest(self, max_quests: int = 10) -> int:
        """
        Accept and complete quests automatically by clicking the quest
        UI elements.

        This is a simplified demonstration. In a production environment,
        you would use template matching to locate quest buttons precisely.

        Args:
            max_quests: Maximum number of quests to process.

        Returns:
            Number of quests processed.
        """
        processed = 0
        logger.info("Starting auto-quest (max=%d)", max_quests)

        for i in range(max_quests):
            if not self._running:
                break
            self._wait_if_paused()

            # Simplified: click predefined quest panel coordinates
            # In practice, use detect_units or find_template for accuracy
            quest_panel_x, quest_panel_y = 1700, 200
            accept_x, accept_y = 1700, 400

            pyautogui.click(quest_panel_x, quest_panel_y)
            time.sleep(QUEST_ACCEPT_DELAY)
            pyautogui.click(accept_x, accept_y)
            processed += 1
            logger.info("Quest %d accepted and submitted", i + 1)
            time.sleep(1.0)

        logger.info("Auto-quest finished: %d quest(s)", processed)
        return processed

    # ── Auto Boss ────────────────────────────────────────────────────────

    def auto_boss(self) -> bool:
        """
        Engage and monitor boss fights, retrying on failure up to
        BOSS_RETRY_COUNT attempts.

        Returns:
            True if a boss was defeated, False otherwise.
        """
        logger.info("Starting auto-boss (max retries=%d)", BOSS_RETRY_COUNT)

        for attempt in range(1, BOSS_RETRY_COUNT + 1):
            if not self._running:
                return False
            self._wait_if_paused()

            # Click the boss engagement button (simplified coordinates)
            boss_btn_x, boss_btn_y = 960, 700
            pyautogui.click(boss_btn_x, boss_btn_y)
            logger.info("Boss engagement attempt %d", attempt)
            time.sleep(BOSS_ENGAGE_DELAY)

            # Monitor HP bar
            defeated = False
            for _ in range(60):  # Poll for up to ~30 seconds
                if not self._running:
                    return False
                self._wait_if_paused()
                screen = capture_screen()
                hp = detect_boss_hp_bar(screen)
                if hp is not None and hp <= BOSS_HEALTH_THRESHOLD:
                    defeated = True
                    break
                time.sleep(0.5)

            if defeated:
                logger.info("Boss defeated on attempt %d", attempt)
                return True

            logger.warning("Boss not defeated on attempt %d, retrying...", attempt)
            time.sleep(2.0)

        logger.error("Auto-boss failed after %d attempts", BOSS_RETRY_COUNT)
        return False

    # ── Main Loop ────────────────────────────────────────────────────────

    def run_cycle(self) -> None:
        """
        Execute one full automation cycle:
        auto-place → auto-roll → auto-quest → auto-boss.
        """
        logger.info("=== Starting automation cycle ===")

        self.auto_place()
        if not self._running:
            return

        self.auto_roll()
        if not self._running:
            return

        self.auto_quest()
        if not self._running:
            return

        self.auto_boss()

        logger.info("=== Automation cycle complete ===")
