"""
config.py – Central configuration for the Anime Reborn automation tool.
All tunable parameters (hotkeys, delays, thresholds) are defined here.
"""

# ── Hotkey Bindings ──────────────────────────────────────────────────────────
START_HOTKEY = "f8"          # Press to start the macro
STOP_HOTKEY  = "f9"          # Press to stop the macro
PAUSE_HOTKEY = "f10"         # Press to pause / resume

# ── Timing & Delays (seconds) ───────────────────────────────────────────────
ROLL_DELAY          = 2.5    # Cooldown between roll actions
QUEST_ACCEPT_DELAY  = 1.0    # Delay before accepting a quest
BOSS_ENGAGE_DELAY   = 3.0    # Delay before engaging a boss
PLACE_UNIT_DELAY    = 0.8    # Delay between placing individual units
FARM_LOOP_PAUSE     = 1.5    # Pause between farm cycle iterations
SCREEN_CAPTURE_INTERVAL = 0.4  # How often the screen is captured (seconds)

# ── Placement Logic ─────────────────────────────────────────────────────────
# Grid dimensions for unit placement (columns x rows)
GRID_COLS = 6
GRID_ROWS = 4
# Preferred slot indices for unit placement (row-major order)
PREFERRED_SLOTS = [0, 1, 2, 6, 7, 8, 12, 13, 14]

# ── Roll Configuration ──────────────────────────────────────────────────────
MAX_ROLLS_PER_SESSION  = 50   # Safety cap on rolls per run
ROLL_PATTERN           = "single"  # Options: "single", "ten_pull"

# ── Boss Configuration ──────────────────────────────────────────────────────
BOSS_RETRY_COUNT      = 3     # Number of retry attempts on boss failure
BOSS_HEALTH_THRESHOLD = 0.15  # Fraction of HP below which the bot considers a boss nearly defeated

# ── Screen Scanner Settings ─────────────────────────────────────────────────
TEMPLATE_MATCH_THRESHOLD = 0.82  # Minimum confidence for template matching (0.0 – 1.0)
SCAN_REGION = None  # (x, y, w, h) tuple or None for full-screen scan

# ── Gem Farm Settings ───────────────────────────────────────────────────────
GEM_FARM_TARGET        = 100000  # Target gem count before stopping
GEM_FARM_QUEST_PRIORITY = ["daily", "weekly", "story"]  # Quest types in priority order

# ── Logging ─────────────────────────────────────────────────────────────────
LOG_LEVEL  = "INFO"       # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE   = "bot_log.txt"
LOG_TO_CONSOLE = True
