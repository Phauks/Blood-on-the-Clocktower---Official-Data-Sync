"""
Shared utilities for interacting with the Blood on the Clocktower wiki.

Provides common functions for fetching and parsing wiki pages.
"""

import sys
import urllib.parse
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scrapers"))

from config import WIKI_BASE_URL
from http_client import fetch_with_retry


def normalize_wiki_name(character_name: str) -> str:
    """Normalize character name for wiki URL.

    Converts character name to wiki-compatible format:
    - Spaces become underscores
    - URL-encode special characters

    Args:
        character_name: Character name (e.g., "Al-Hadikhia")

    Returns:
        Normalized name for wiki URL (e.g., "Al-Hadikhia")
    """
    # Replace spaces with underscores
    wiki_name = character_name.replace(" ", "_")

    # URL-encode special characters (but keep underscores)
    wiki_name = urllib.parse.quote(wiki_name, safe="_")

    return wiki_name


def construct_wiki_url(character_name: str, validate: bool = True) -> str:
    """Construct full wiki URL for a character.

    Args:
        character_name: Character name
        validate: If True, perform SSRF protection validation

    Returns:
        Full wiki URL

    Raises:
        ValueError: If validation fails
    """
    wiki_name = normalize_wiki_name(character_name)
    url = f"{WIKI_BASE_URL}/{wiki_name}"

    if validate:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Invalid URL scheme: {parsed.scheme}")
        if not parsed.netloc.endswith("bloodontheclocktower.com"):
            raise ValueError(f"URL does not match expected domain: {url}")

    return url


def fetch_wiki_page(character_name: str, char_id: str | None = None) -> str | None:
    """Fetch wiki page HTML for a character.

    Args:
        character_name: Character name
        char_id: Optional character ID for logging

    Returns:
        HTML content as string, or None if fetch failed
    """
    url = construct_wiki_url(character_name)
    response = fetch_with_retry(url)

    if response is None:
        return None

    return response.text


def rate_limit(delay: float) -> None:
    """Sleep for rate limiting.

    Convenience function for rate limiting wiki requests.

    Args:
        delay: Delay in seconds
    """
    import time

    time.sleep(delay)
