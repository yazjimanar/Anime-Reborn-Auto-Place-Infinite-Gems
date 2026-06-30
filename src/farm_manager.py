"""
farm_manager.py – Manages infinite gems farming, crafting automation,
and unit upgrade workflows.
"""

import time
from typing import Optional

from bot import AnimeRebornBot
from config import (
    GEM_FARM_TARGET,
    GEM_FARM_QUEST_PRIORITY,
    FARM_LOOP_PAUSE,
)
from utils import setup_logger, resolve_path

logger = setup_logger("farm_manager")


class FarmManager:
    """
    Orchestrates extended farming sessions that combine quest completion,
    boss fights, and auto-roll to accumulate gems toward a target.
    """

    def __init__(self, bot: Optional[AnimeRebornBot] = None) -> None:
        """
        Initialize the FarmManager.

        Args:
            bot: An AnimeRebornBot instance, or None to create one.
        """
        self.bot = bot or AnimeRebornBot()
        self._gems_collected = 0
        self._cycles_completed = 0

    @property
    def gems_collected(self) -> int:
        """Return the estimated total gems collected this session."""
        return self._gems_collected

    @property
    def cycles_completed(self) -> int:
        """Return the number of full farm cycles completed."""
        return self._cycles_completed

    # ── Gem Estimation ───────────────────────────────────────────────────

    def _estimate_gems_from_cycle(self) -> int:
        """
        Estimate gems earned from one cycle based on quest types completed.

        These values are placeholders for educational demonstration.
        In a real scenario, you would read gem counts from the screen.

        Returns:
            Estimated gem count for the cycle.
        """
        gem_map = {"daily": 500, "weekly": 2000, "story": 300, "boss": 1000}
        estimated = 0
        for q_type in GEM_FARM_QUEST_PRIORITY:
            estimated += gem_map.get(q_type, 100)
        # Add boss reward
        estimated += gem_map.get("boss", 1000)
        return estimated

    # ── Crafting Automation ───────────────────────────────────────────────

    def auto_craft(self, iterations: int = 5) -> int:
        """
        Simulate automated crafting by clicking through the crafting UI.

        Args:
            iterations: Number of craft actions to perform.

        Returns:
            Number of crafts completed.
        """
        import pyautogui

        crafted = 0
        logger.info("Starting auto-craft (iterations=%d)", iterations)

        # Simplified crafting coordinates (would use template matching in production)
        craft_open_x, craft_open_y = 1500, 900
        craft_btn_x, craft_btn_y = 960, 600
        confirm_x, confirm_y = 1000, 700

        for i in range(iterations):
            if not self.bot.is_running:
                break

            pyautogui.click(craft_open_x, craft_open_y)
            time.sleep(0.8)
            pyautogui.click(craft_btn_x, craft_btn_y)
            time.sleep(0.5)
            pyautogui.click(confirm_x, confirm_y)
            crafted += 1
            logger.debug("Craft %d completed", i + 1)
            time.sleep(1.2)

        logger.info("Auto-craft finished: %d item(s) crafted", crafted)
        return crafted

    # ── Unit Upgrade ─────────────────────────────────────────────────────

    def auto_upgrade_units(self, max_upgrades: int = 10) -> int:
        """
        Automate unit upgrade actions by clicking through the upgrade UI.

        Args:
            max_upgrades: Maximum number of upgrade actions.

        Returns:
            Number of upgrades performed.
        """
        import pyautogui

        upgraded = 0
        logger.info("Starting auto-upgrade (max=%d)", max_upgrades)

        # Simplified upgrade coordinates
        unit_select_x, unit_select_y = 200, 400
        upgrade_btn_x, upgrade_btn_y = 1400, 800

        for i in range(max_upgrades):
            if not self.bot.is_running:
                break

            pyautogui.click(unit_select_x, unit_select_y)
            time.sleep(0.5)
            pyautogui.click(upgrade_btn_x, upgrade_btn_y)
            upgraded += 1
            logger.debug("Upgrade %d performed", i + 1)
            time.sleep(1.0)

        logger.info("Auto-upgrade finished: %d upgrade(s)", upgraded)
        return upgraded

    # ── Main Farm Loop ───────────────────────────────────────────────────

    def run_farm_session(self, target_gems: Optional[int] = None) -> None:
        """
        Run a continuous farming session until the gem target is reached
        or the bot is stopped.

        Args:
            target_gems: Gem target, or None to use the configured default.
        """
        target = target_gems if target_gems is not None else GEM_FARM_TARGET
        self._gems_collected = 0
        self._cycles_completed = 0

        logger.info(
            "Starting farm session – target: %d gems", target
        )
        self.bot.start()

        try:
            while self._gems_collected < target and self.bot.is_running:
                self.bot.run_cycle()
                self._cycles_completed += 1

                cycle_gems = self._estimate_gems_from_cycle()
                self._gems_collected += cycle_gems

                logger.info(
                    "Cycle %d complete – estimated total gems: %d / %d",
                    self._cycles_completed,
                    self._gems_collected,
                    target,
                )

                # Optional: run crafting and upgrades periodically
                if self._cycles_completed % 3 == 0:
                    self.auto_craft(iterations=3)
                    self.auto_upgrade_units(max_upgrades=5)

                time.sleep(FARM_LOOP_PAUSE)

        except KeyboardInterrupt:
            logger.info("Farm session interrupted by user")
        finally:
            self.bot.stop()
            logger.info(
                "Farm session ended – cycles: %d, gems: %d / %d",
                self._cycles_completed,
                self._gems_collected,
                target,
            )
