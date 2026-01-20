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
ASYNC_REQUEST_TIMEOUT = 30  # seconds for aiohttp
RATE_LIMIT_SECONDS = 1.0  # delay between wiki requests
HTTP_MAX_RETRIES = 3  # retry attempts on transient failures
HTTP_RETRY_BACKOFF = 1.0  # base backoff time (exponential: 1s, 2s, 4s)
HTTP_MAX_SIZE = 10 * 1024 * 1024  # 10 MB - max response size
USER_AGENT = (
    "BOTC-Data-Sync/1.0 (https://github.com/Phauks/Blood-on-the-Clocktower---Official-Data-Sync)"
)

# =============================================================================
# Browser settings (Playwright)
# =============================================================================
DEFAULT_TIMEOUT = 60000  # 60 seconds
PAGE_RENDER_DELAY = 2000  # 2 seconds for SPA to render
CLICK_DELAY = 500  # 500ms after adding characters

# Characters that need setup: true but don't have bracket text in their ability
# Most setup characters are detected via [bracket text] patterns automatically
SETUP_EXCEPTIONS = {
    "drunk",  # False identity: "You do not know you are the Drunk"
    "sentinel",  # Fabled with prose: "might be 1 extra or 1 fewer Outsider"
    "deusexfiasco",  # Fabled: Storyteller makes mistakes
}

# Valid editions
VALID_EDITIONS = {"tb", "bmr", "snv", "carousel", "fabled", "loric"}

# Valid team types
VALID_TEAMS = {"townsfolk", "outsider", "minion", "demon", "traveller", "fabled", "loric"}

# =============================================================================
# Batch processing settings
# =============================================================================
WIKI_FETCH_BATCH_SIZE = 5  # concurrent wiki requests
DOWNLOAD_BATCH_SIZE = 10  # concurrent icon downloads
IMAGE_RATE_LIMIT = 0.2  # delay between icon downloads (seconds)

# =============================================================================
# Validation settings
# =============================================================================
EXPECTED_TOTAL_CHARACTERS = 174  # Total characters across all editions
MAX_ABILITY_LENGTH = 500  # characters
MAX_NAME_LENGTH = 30  # characters (for schema validation)
MAX_INPUT_NAME_LENGTH = 100  # characters (security limit for user input)
MAX_REMINDER_LENGTH = 30  # characters
MAX_REMINDER_COUNT = 10  # tokens per character
MIN_FLAVOR_LENGTH = 3  # minimum valid flavor text

# Character name pattern for wiki URLs (letters, numbers, spaces, hyphens, apostrophes, accented chars)
CHARACTER_NAME_PATTERN = r"^[a-zA-Z0-9\s\-'À-ÿ]+$"

# =============================================================================
# Schema version
# =============================================================================
SCHEMA_VERSION = 1  # increment on breaking data format changes
