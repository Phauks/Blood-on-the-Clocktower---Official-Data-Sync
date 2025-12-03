"""
Parser utilities for Blood on the Clocktower scraper.

Functions for parsing icon URLs, detecting setup flags, and text processing.
"""

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

# Handle both direct script execution and module import
try:
    from .config import BASE_ICON_URL, SETUP_EXCEPTIONS, WIKI_BASE_URL
except ImportError:
    from config import BASE_ICON_URL, SETUP_EXCEPTIONS, WIKI_BASE_URL

# Add utils to path for logger
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from logger import get_logger

logger = get_logger(__name__)


def parse_edition_from_icon(icon_src: str) -> str:
    """Extract edition from icon path.

    Example: "src/assets/icons/tb/washerwoman_g.webp" -> "tb"
    """
    match = re.search(r"/icons/([^/]+)/", icon_src)
    return match.group(1) if match else "unknown"


def parse_character_id_from_icon(icon_src: str) -> str | None:
    """Extract character ID from icon path.

    Examples:
        "src/assets/icons/carousel/bountyhunter_g.webp" -> "bountyhunter"
        "src/assets/icons/tb/spy_e.webp" -> "spy"
        "src/assets/icons/fabled/djinn.webp" -> "djinn"
    """
    match = re.search(r"/icons/[^/]+/([a-z]+?)(?:_[ge])?\.webp", icon_src)
    return match.group(1) if match else None


def construct_full_icon_url(icon_src: str) -> str:
    """Convert relative icon path to full URL."""
    if icon_src.startswith("http"):
        return icon_src
    # Remove leading "./" or "src/" if present
    clean_path = icon_src.lstrip("./")
    if not clean_path.startswith("src/"):
        clean_path = (
            f"src/{clean_path}" if not clean_path.startswith("assets/") else f"src/{clean_path}"
        )
    return f"{BASE_ICON_URL}{clean_path}"


def construct_local_image_path(edition: str, char_id: str, icon_src: str) -> str:
    """Construct local image path for a character.

    Args:
        edition: Edition ID (e.g., "tb", "bmr")
        char_id: Character ID (e.g., "washerwoman")
        icon_src: Original icon source URL (to extract file extension)

    Returns:
        Local path like "icons/tb/washerwoman.webp"

    Raises:
        ValueError: If edition or char_id contains invalid characters (path traversal attempt)

    Security:
        Validates inputs to prevent directory traversal attacks
    """
    # Sanitize inputs - only allow lowercase alphanumeric, hyphens, and underscores
    # This prevents path traversal attacks like "../../../etc/passwd"
    if not re.match(r"^[a-z0-9_-]+$", edition):
        raise ValueError(
            f"Invalid edition name: {edition!r}. Must contain only lowercase letters, numbers, hyphens, and underscores."
        )

    if not re.match(r"^[a-z0-9_-]+$", char_id):
        raise ValueError(
            f"Invalid character ID: {char_id!r}. Must contain only lowercase letters, numbers, hyphens, and underscores."
        )

    # Validate and extract extension from icon source
    allowed_extensions = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".svg"}
    ext = ".webp"  # Default extension

    if "." in icon_src:
        # Extract extension safely using Path
        try:
            ext_candidate = Path(icon_src).suffix.lower()
            if ext_candidate in allowed_extensions:
                ext = ext_candidate
        except (ValueError, OSError) as e:
            # If Path parsing fails, use default .webp
            logger.debug(f"Failed to parse extension from {icon_src}: {e}")

    return f"icons/{edition}/{char_id}{ext}"


def detect_setup_flag(character_id: str, ability_text: str) -> bool:
    """Detect if a character requires setup: true.

    Setup characters have [bracket text] in their ability that modifies
    game composition (e.g., [+2 Outsiders], [No evil characters], [+the King]).

    A few exceptions exist for characters without bracket text.
    """
    # Check exception list (characters without bracket text)
    if character_id in SETUP_EXCEPTIONS:
        return True

    # Primary detection: any bracket text indicates setup modification
    return bool(re.search(r"\[.*\]", ability_text))


def character_name_to_wiki_url(name: str) -> str:
    """Convert character name to wiki URL.

    Example: "Fortune Teller" -> "https://wiki.bloodontheclocktower.com/Fortune_Teller"

    Args:
        name: Character name (e.g., "Fortune Teller", "Al-Hadikhia")

    Returns:
        Full wiki URL

    Raises:
        ValueError: If name is too long or contains suspicious characters

    Security:
        Validates character name length and format to prevent SSRF attacks
    """
    # Validate name is reasonable
    if not name or len(name) > 100:
        raise ValueError(f"Invalid character name length: {len(name)}")

    # Check for suspicious characters that might indicate injection attempt
    # Allow: letters, numbers, spaces, hyphens, apostrophes, accented characters
    if not re.match(r"^[a-zA-Z0-9\s\-'À-ÿ]+$", name):
        raise ValueError(f"Invalid characters in character name: {name!r}")

    # URL-encode the name safely
    wiki_name = name.replace(" ", "_").replace("'", "%27")
    url = f"{WIKI_BASE_URL}/{wiki_name}"

    # Validate final URL matches expected domain
    parsed = urlparse(url)
    if not parsed.netloc.endswith("bloodontheclocktower.com"):
        raise ValueError(f"Generated URL does not match expected domain: {url}")

    return url
