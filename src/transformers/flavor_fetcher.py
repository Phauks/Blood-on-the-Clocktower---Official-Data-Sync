"""
Blood on the Clocktower - Flavor Text Fetcher (Incremental)

Fetches flavor text from the BOTC wiki with smart caching.
Only fetches when necessary:
- New character added
- Character ability changed
- Flavor text currently empty

This minimizes wiki requests from total character count to only when necessary.
"""

import json
import time

from tqdm import tqdm

from src.scrapers.config import CHARACTERS_DIR, RATE_LIMIT_SECONDS
from src.scrapers.writers import order_character_fields, strip_internal_fields
from src.utils.data_loader import load_previous_character_data
from src.utils.http_client import fetch_with_retry
from src.utils.logger import get_logger
from src.utils.wiki_client import construct_wiki_url

logger = get_logger(__name__)


def is_valid_flavor(flavor: str) -> bool:
    """Check if flavor text is valid (not garbage HTML or malformed).

    Args:
        flavor: Flavor text to validate

    Returns:
        bool: True if flavor is valid
    """
    if not flavor:
        return False

    # Check for garbage HTML patterns
    garbage_patterns = [
        ">\n<head>",
        "<meta charset",
        "<!DOCTYPE",
        "<html",
        "<script",
    ]

    if any(pattern in flavor for pattern in garbage_patterns):
        return False

    # Valid flavor should start with a quote and be at least 3 chars (e.g., "...")
    return flavor.startswith('"') and len(flavor) >= 3


def needs_flavor_update(character: dict, previous_data: dict[str, dict]) -> bool:
    """Determine if we need to fetch flavor text for this character.

    Args:
        character: Current character object (just scraped)
        previous_data: Character data from previous run

    Returns:
        bool: True if flavor text fetch is needed
    """
    char_id = character["id"]

    # Case 1: New character (not in previous data)
    if char_id not in previous_data:
        return True

    previous = previous_data[char_id]

    # Case 2: Flavor text is missing, empty, or invalid (garbage HTML)
    current_flavor = character.get("flavor", "")
    previous_flavor = previous.get("flavor", "")

    if not is_valid_flavor(current_flavor) and not is_valid_flavor(previous_flavor):
        # Both missing or invalid - need to fetch
        return True

    # Case 3: Previous flavor is garbage - need to re-fetch
    if previous_flavor and not is_valid_flavor(previous_flavor):
        return True

    # Case 4: Character ability changed (might have new flavor)
    if character.get("ability", "") != previous.get("ability", ""):
        return True

    # Case 5: Character name changed (wiki URL would change)
    # Otherwise, no update needed
    return character.get("name", "") != previous.get("name", "")


def preserve_flavor_text(character: dict, previous_data: dict[str, dict]) -> bool:
    """Copy flavor text from previous data if available and valid.

    Args:
        character: Current character object to update
        previous_data: Character data from previous run

    Returns:
        bool: True if flavor was preserved
    """
    char_id = character["id"]

    if char_id in previous_data:
        previous_flavor = previous_data[char_id].get("flavor", "")
        if is_valid_flavor(previous_flavor):
            character["flavor"] = previous_flavor
            return True

    return False


def extract_flavor_from_html(html: str) -> str | None:
    """Extract flavor text from wiki page HTML.

    The flavor text appears in italics after the character infobox,
    typically in a format like: "Quoted flavor text here."

    Args:
        html: Raw HTML content from wiki page

    Returns:
        Extracted flavor text or None if not found
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    # Strategy 1: Find the main content area and look for italic text with quotes
    content = soup.find("div", {"id": "mw-content-text"}) or soup.find(
        "div", {"class": "mw-parser-output"}
    )
    if not content:
        content = soup

    # Skip patterns for ability text - these are game mechanic phrases
    ability_patterns = [
        "you start knowing",  # Common ability opener
        "each night,",  # Night ability
        "each night*,",  # Night ability with asterisk
        "once per game,",  # Limited ability
        "you are drunk",  # Drunk/poisoned
        "you are poisoned",  # Drunk/poisoned
        "you think you are",  # Lunatic-style
        "you may nominate",  # Nomination ability
        "players may not",  # Restriction ability
        "if you die,",  # Death trigger (specific format)
        "when you die,",  # Death trigger (specific format)
        "on your 1st night",  # First night specific
        "the 1st time",  # First occurrence
    ]

    # Helper function to normalize quotes
    def normalize_quotes(text: str) -> str:
        """Replace curly quotes with straight quotes."""
        return (
            text.replace("\u201c", '"')
            .replace("\u201d", '"')
            .replace("\u2018", "'")
            .replace("\u2019", "'")
        )

    # Strategy 1: Look for <p class="flavour"> element (new wiki format)
    flavour_elem = content.find("p", class_="flavour")
    if flavour_elem:
        text = normalize_quotes(flavour_elem.get_text(strip=True))
        if text:
            # Ensure it's wrapped in quotes (but not double-wrapped)
            if text.startswith('"') and text.endswith('"'):
                return text  # Already properly quoted
            elif not text.startswith('"'):
                text = f'"{text}"'
            elif not text.endswith('"'):
                text = text + '"'
            return text

    # Strategy 2: Look for italic elements that contain quoted text (flavor format)
    # Some flavors are very short (e.g., "Die." for Slayer, "..." for Assassin)
    for italic in content.find_all(["i", "em"]):
        text = normalize_quotes(italic.get_text(strip=True))
        # Flavor text is typically in quotes - can be as short as 3 chars ("...")
        if text.startswith('"') and text.endswith('"') and 3 <= len(text) <= 500:
            # Skip ability text patterns
            lower_text = text.lower()
            if any(skip in lower_text for skip in ability_patterns):
                continue
            return text

    # Strategy 3: Look for non-English flavor text (e.g., Japanese for Shugenja)
    # These may not be in quotes but are in italic after the infobox
    infobox = content.find("table", class_="infobox")
    if infobox:
        # Look for italic text immediately after infobox
        for sibling in infobox.find_next_siblings():
            if sibling.name in ["h2", "h3"]:
                break  # Stop at next section
            italic = sibling.find("i") or sibling.find("em")
            if italic:
                text = italic.get_text(strip=True)
                # Check for non-ASCII (non-English) text that isn't already captured
                if text and not text.startswith('"') and any(ord(c) > 127 for c in text):
                    # Non-English flavor text (e.g., Japanese)
                    return f'"{text}"'  # Wrap in quotes for consistency

    # Strategy 4: Look for quoted text directly after the infobox
    for p in content.find_all("p"):
        text = normalize_quotes(p.get_text(strip=True))
        if text.startswith('"') and 3 <= len(text) <= 500:
            # Check it's not ability text
            lower_text = text.lower()
            if any(skip in lower_text for skip in ability_patterns):
                continue
            # Extract just the quoted portion
            end_quote = text.find('"', 1)
            if end_quote > 0:
                return text[: end_quote + 1]

    return None


def fetch_flavor_from_wiki(char_name: str) -> str | None:
    """Fetch flavor text from the BOTC wiki for a character.

    Args:
        char_name: Character name (used in wiki URL)

    Returns:
        Flavor text or None if not found
    """
    # Construct wiki URL using shared utility
    url = construct_wiki_url(char_name)

    response = fetch_with_retry(url)
    if response is None:
        return None

    flavor = extract_flavor_from_html(response.text)
    return flavor


def update_flavor_for_characters(characters: dict[str, dict], force: bool = False) -> dict:
    """Update flavor text for all characters that need it.

    Args:
        characters: Dict of character data to update
        force: If True, fetch all flavor texts regardless of cache

    Returns:
        dict with stats: {"fetched": int, "preserved": int, "failed": int}
    """
    previous_data = load_previous_character_data()

    stats = {"fetched": 0, "preserved": 0, "failed": 0, "skipped": 0}

    logger.info(f"Loaded {len(previous_data)} characters from previous data")
    logger.info("Checking flavor text updates...")

    # First pass: identify characters that need fetching
    to_fetch = []
    for char_id, character in characters.items():
        if not force and not needs_flavor_update(character, previous_data):
            # Preserve existing flavor
            if preserve_flavor_text(character, previous_data):
                stats["preserved"] += 1
            else:
                stats["skipped"] += 1
        else:
            to_fetch.append((char_id, character))

    # Second pass: fetch with progress bar
    if to_fetch:
        pbar = tqdm(to_fetch, desc="Fetching flavor", unit="char")
        for char_id, character in pbar:
            char_name = character.get("name", char_id)
            pbar.set_postfix_str(char_name[:20])

            flavor = fetch_flavor_from_wiki(char_name)

            if flavor:
                character["flavor"] = flavor
                stats["fetched"] += 1
            else:
                # Try to preserve previous flavor on failure
                if preserve_flavor_text(character, previous_data):
                    stats["failed"] += 1
                else:
                    character["flavor"] = ""
                    stats["failed"] += 1

            # Rate limiting - be nice to the wiki server
            time.sleep(RATE_LIMIT_SECONDS)

    logger.info("\nFlavor text summary:")
    logger.info(f"  Fetched: {stats['fetched']}")
    logger.info(f"  Preserved: {stats['preserved']}")
    logger.info(f"  Failed: {stats['failed']}")
    logger.info(f"  Skipped: {stats['skipped']}")

    return stats


def save_updated_characters(characters: dict[str, dict]) -> None:
    """Save characters with updated flavor text back to files."""
    for char_id, character in characters.items():
        edition = character.get("edition", "unknown")
        edition_dir = CHARACTERS_DIR / edition
        edition_dir.mkdir(parents=True, exist_ok=True)

        # Order fields and save
        ordered_char = order_character_fields(character)
        char_file = edition_dir / f"{char_id}.json"
        with open(char_file, "w", encoding="utf-8") as f:
            json.dump(ordered_char, f, indent=2, ensure_ascii=False)

    # Update combined file (strip internal fields, order fields)
    all_chars = []
    for char in characters.values():
        clean_char = strip_internal_fields(char, preserve_reminder_flag=False)
        ordered_char = order_character_fields(clean_char)
        all_chars.append(ordered_char)

    all_file = CHARACTERS_DIR / "all_characters.json"
    with open(all_file, "w", encoding="utf-8") as f:
        json.dump(all_chars, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(characters)} characters with flavor text")


def load_scraped_characters() -> dict[str, dict]:
    """Load characters from the combined all_characters.json file."""
    all_file = CHARACTERS_DIR / "all_characters.json"

    if not all_file.exists():
        raise FileNotFoundError(
            f"Character data not found at {all_file}. Run character_scraper.py first."
        )

    with open(all_file, encoding="utf-8") as f:
        characters_list = json.load(f)

    return {char["id"]: char for char in characters_list}


def main():
    """Main entry point for standalone flavor fetching."""
    import argparse

    parser = argparse.ArgumentParser(description="Fetch flavor text for BOTC characters")
    parser.add_argument("--force", action="store_true", help="Force fetch all flavor texts")
    args = parser.parse_args()

    # Load scraped character data
    logger.info("Loading character data...")
    characters = load_scraped_characters()
    logger.info(f"Loaded {len(characters)} characters")

    # Update flavor text
    logger.info("\n--- Updating flavor text ---")
    stats = update_flavor_for_characters(characters, force=args.force)

    # Save if any fetches were made
    if stats["fetched"] > 0:
        logger.info("\n--- Saving updated characters ---")
        save_updated_characters(characters)
    else:
        logger.info("\nNo new flavor text fetched, skipping save.")

    logger.info("\n✓ Flavor text update complete!")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
