"""
Shared utilities for interacting with the Blood on the Clocktower wiki.

Provides common functions for fetching and parsing wiki pages.
"""

import re
import urllib.parse

from src.scrapers.config import (
    CHARACTER_NAME_PATTERN,
    MAX_INPUT_NAME_LENGTH,
    WIKI_BASE_URL,
)
from src.utils.http_client import fetch_with_retry


def validate_character_name(char_name: str) -> None:
    """Validate character name for wiki URL construction.

    Args:
        char_name: Character name to validate

    Raises:
        ValueError: If character name is invalid or potentially malicious

    Security:
        - Validates length to prevent buffer overflow attacks
        - Validates pattern to prevent URL injection attacks
    """
    if not char_name:
        raise ValueError("Character name cannot be empty")

    if len(char_name) > MAX_INPUT_NAME_LENGTH:
        raise ValueError(f"Character name too long: {len(char_name)} > {MAX_INPUT_NAME_LENGTH}")

    # Check for suspicious characters (allow letters, numbers, spaces, hyphens, apostrophes, accents)
    if not re.match(CHARACTER_NAME_PATTERN, char_name):
        raise ValueError(f"Invalid characters in character name: {char_name!r}")


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
        # Use explicit whitelist to prevent subdomain attacks
        # (e.g., evil.bloodontheclocktower.com or evilbloodontheclocktower.com)
        valid_domains = {"wiki.bloodontheclocktower.com", "script.bloodontheclocktower.com"}
        if parsed.netloc not in valid_domains:
            raise ValueError(f"URL does not match allowed domains: {url}")

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
