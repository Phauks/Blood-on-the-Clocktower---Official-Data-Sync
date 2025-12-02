"""
Parser utilities for Blood on the Clocktower scraper.

Functions for parsing icon URLs, detecting setup flags, and text processing.
"""

import re

# Handle both direct script execution and module import
try:
    from .config import SETUP_CHARACTERS, BASE_ICON_URL, WIKI_BASE_URL
except ImportError:
    from config import SETUP_CHARACTERS, BASE_ICON_URL, WIKI_BASE_URL


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
        clean_path = f"src/{clean_path}" if not clean_path.startswith("assets/") else f"src/{clean_path}"
    return f"{BASE_ICON_URL}{clean_path}"


def construct_local_image_path(edition: str, char_id: str, icon_src: str) -> str:
    """Construct local image path for a character.
    
    Args:
        edition: Edition ID (e.g., "tb", "bmr")
        char_id: Character ID (e.g., "washerwoman")
        icon_src: Original icon source URL (to extract file extension)
    
    Returns:
        Local path like "icons/tb/washerwoman.webp"
    """
    # Extract extension from original URL, default to .webp
    ext = ".webp"
    if "." in icon_src:
        ext = "." + icon_src.rsplit(".", 1)[-1]
    
    return f"icons/{edition}/{char_id}{ext}"


def detect_setup_flag(character_id: str, ability_text: str) -> bool:
    """Detect if a character requires setup: true.
    
    Uses hybrid approach:
    1. Check explicit list (most reliable)
    2. Pattern matching on ability text (catches new characters)
    """
    # Check explicit list first
    if character_id in SETUP_CHARACTERS:
        return True
    
    ability_lower = ability_text.lower()
    
    # Pattern 1: False identity
    false_identity_patterns = [
        r"you do not know you are",
        r"you think you are",
        r"you think you have",
    ]
    for pattern in false_identity_patterns:
        if re.search(pattern, ability_lower):
            return True
    
    # Pattern 2: Setup text in brackets [+N Outsider], [1 Townsfolk is evil], etc.
    if re.search(r"\[[^\]]*(?:outsider|townsfolk|minion|demon|evil|good)[^\]]*\]", ability_lower):
        return True
    
    return False


def character_name_to_wiki_url(name: str) -> str:
    """Convert character name to wiki URL.
    
    Example: "Fortune Teller" -> "https://wiki.bloodontheclocktower.com/Fortune_Teller"
    """
    wiki_name = name.replace(" ", "_").replace("'", "%27")
    return f"{WIKI_BASE_URL}{wiki_name}"
