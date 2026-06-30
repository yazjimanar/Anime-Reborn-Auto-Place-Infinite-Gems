"""
main.py – Entry point for the Anime Reborn automation tool.
Initializes the bot, sets up hotkey listeners, and manages the runtime loop.
"""

import sys
import signal

import keyboard

from config import (
    START_HOTKEY,
    STOP_HOTKEY,
    PAUSE_HOTKEY,
    LOG_LEVEL,
    LOG_FILE,
    LOG_TO_CONSOLE,
    GEM_FARM_TARGET,
)
from utils import setup_logger, require_admin
from bot import AnimeRebornBot
from farm_manager import FarmManager

# ── Initialize Logger ────────────────────────────────────────────────────────
logger = setup_logger(
    name="main",
    level=LOG_LEVEL,
    log_file=LOG_FILE,
    console=LOG_TO_CONSOLE,
)


def main() -> None:
    """
    Main entry point: check privileges, create bot and farm manager,
    register hotkeys, and wait for user input.
    """
    logger.info("Anime Reborn Automation Tool – Starting...")

    # Verify elevated privileges for reliable screen capture
    require_admin()

    # Create core instances
    bot = AnimeRebornBot()
    farm = FarmManager(bot=bot)

    # ── Hotkey Handlers ──────────────────────────────────────────────────

    def on_start() -> None:
        """Handle the start hotkey – launch a farm session."""
        logger.info("Start hotkey (%s) pressed – launching farm session", START_HOTKEY)
        try:
            farm.run_farm_session(target_gems=GEM_FARM_TARGET)
        except Exception as exc:
            logger.error("Farm session error: %s", exc)

    def on_stop() -> None:
        """Handle the stop hotkey – immediately stop the bot."""
        logger.info("Stop hotkey (%s) pressed – stopping bot", STOP_HOTKEY)
        bot.stop()

    def on_pause() -> None:
        """Handle the pause hotkey – toggle pause state."""
        logger.info("Pause hotkey (%s) pressed – toggling pause", PAUSE_HOTKEY)
        bot.pause()

    # ── Register Hotkeys ─────────────────────────────────────────────────
    try:
        keyboard.add_hotkey(START_HOTKEY, on_start, suppress=True)
        keyboard.add_hotkey(STOP_HOTKEY, on_stop, suppress=True)
        keyboard.add_hotkey(PAUSE_HOTKEY, on_pause, suppress=True)
    except Exception as exc:
        logger.error("Failed to register hotkeys: %s", exc)
        sys.exit(1)

    logger.info("Hotkeys registered:")
    logger.info("  [%s] Start farm session", START_HOTKEY.upper())
    logger.info("  [%s] Stop bot", STOP_HOTKEY.upper())
    logger.info("  [%s] Pause / Resume", PAUSE_HOTKEY.upper())
    logger.info("Press Ctrl+C to exit the program.")

    # ── Graceful Shutdown ────────────────────────────────────────────────

    def signal_handler(sig, frame) -> None:  # type: ignore[no-untyped-def]
        """Handle SIGINT (Ctrl+C) for clean shutdown."""
        logger.info("Shutdown signal received")
        bot.stop()
        keyboard.unhook_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # ── Keep the Process Alive ───────────────────────────────────────────
    try:
        keyboard.wait()  # Blocks until a registered hotkey triggers exit
    except KeyboardInterrupt:
        pass
    finally:
        bot.stop()
        keyboard.unhook_all()
        logger.info("Anime Reborn Automation Tool – Exited cleanly")


if __name__ == "__main__":
    main()
