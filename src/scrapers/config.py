"""
Configuration constants for Blood on the Clocktower scrapers.

All shared constants should be defined here and imported by other modules.
"""

from pathlib import Path

# =============================================================================
# URLs
# =============================================================================
SCRIPT_TOOL_URL = "https://script.bloodontheclocktower.com/"
BASE_ICON_URL = "https://script.bloodontheclocktower.com/"
WIKI_BASE_URL = "https://wiki.bloodontheclocktower.com"

# =============================================================================
# Output paths
# =============================================================================
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHARACTERS_DIR = DATA_DIR / "characters"
DIST_DIR = PROJECT_ROOT / "dist"
ICONS_DIR = DIST_DIR / "icons"  # Icons stored directly in dist for packaging

# =============================================================================
# HTTP settings (used by all fetchers)
# =============================================================================
REQUEST_TIMEOUT = 30  # seconds
RATE_LIMIT_SECONDS = 1.0  # delay between wiki requests
HTTP_MAX_RETRIES = 3  # retry attempts on transient failures
HTTP_RETRY_BACKOFF = 1.0  # base backoff time (exponential: 1s, 2s, 4s)
USER_AGENT = "BOTC-Data-Sync/1.0 (https://github.com/Phauks/Blood-on-the-Clocktower---Official-Data-Sync)"

# =============================================================================
# Browser settings (Playwright)
# =============================================================================
DEFAULT_TIMEOUT = 60000  # 60 seconds
PAGE_RENDER_DELAY = 2000  # 2 seconds for SPA to render
CLICK_DELAY = 500  # 500ms after adding characters

# Characters known to require setup: true (explicit list for reliability)
# These characters modify game setup (add/remove players, change roles, etc.)
SETUP_CHARACTERS = {
    # Trouble Brewing
    "drunk",
    "baron",
    # Bad Moon Rising
    "lunatic",
    "godfather",
    # Sects & Violets
    # (none in base S&V)
    # Experimental (Carousel)
    "bountyhunter",
    "villageidiot",
    "kazali",
    "legion",
    "riot",
    "atheist",
    "lilmonsta",
    "marionette",
    "summoner",
    "poppygrower",
    "magician",
    "snitch",
    "damsel",
    "heretic",
    "sentinel",
    "balloonist",
    "cultleader",
    "organgrinder",
    "xaan",
}

# Valid editions
VALID_EDITIONS = {"tb", "bmr", "snv", "carousel", "fabled", "loric"}

# Valid team types
VALID_TEAMS = {"townsfolk", "outsider", "minion", "demon", "traveller", "fabled", "loric"}
