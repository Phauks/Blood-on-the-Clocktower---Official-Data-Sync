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
import re
import sys
import time
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scrapers"))
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

# Import from config (consolidated constants)
from config import (
    WIKI_BASE_URL,
    CHARACTERS_DIR,
    RATE_LIMIT_SECONDS,
)

# Import shared utilities
from http_client import fetch_with_retry
from data_loader import load_previous_character_data


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
    
    # Case 2: Flavor text is missing or empty
    current_flavor = character.get("flavor", "")
    if not current_flavor:
        previous_flavor = previous.get("flavor", "")
        if not previous_flavor:
            # Both empty - need to fetch
            return True
    
    # Case 3: Character ability changed (might have new flavor)
    if character.get("ability", "") != previous.get("ability", ""):
        return True
    
    # Case 4: Character name changed (wiki URL would change)
    if character.get("name", "") != previous.get("name", ""):
        return True
    
    # Otherwise, no update needed
    return False


def preserve_flavor_text(character: dict, previous_data: dict[str, dict]) -> bool:
    """Copy flavor text from previous data if available.
    
    Args:
        character: Current character object to update
        previous_data: Character data from previous run
    
    Returns:
        bool: True if flavor was preserved
    """
    char_id = character["id"]
    
    if char_id in previous_data:
        previous_flavor = previous_data[char_id].get("flavor", "")
        if previous_flavor:
            character["flavor"] = previous_flavor
            return True
    
    return False


def extract_flavor_from_html(html: str) -> str | None:
    """Extract flavor text from wiki page HTML.
    
    The flavor text is typically in an italicized paragraph near the top
    of the character page, often in a blockquote or specific div.
    
    Args:
        html: Raw HTML content from wiki page
    
    Returns:
        Extracted flavor text or None if not found
    """
    # Strategy 1: Look for the main content area's first italic text
    # Wiki pages typically have flavor in <i> or <em> tags
    
    # Try to find flavor in common wiki structures
    patterns = [
        # Pattern 1: Blockquote with italic
        r'<blockquote[^>]*>\s*<p>\s*<i>([^<]+)</i>',
        # Pattern 2: Direct italic paragraph
        r'<p>\s*<i>([^<]{20,200})</i>\s*</p>',
        # Pattern 3: em tags
        r'<p>\s*<em>([^<]{20,200})</em>\s*</p>',
        # Pattern 4: Class-based flavor container
        r'class="[^"]*flavor[^"]*"[^>]*>([^<]+)<',
        # Pattern 5: Quote marks around text
        r'"([^"]{20,200})"',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
        for match in matches:
            # Clean up the match
            flavor = match.strip()
            # Skip if it looks like navigation or ability text
            if any(skip in flavor.lower() for skip in [
                "you start", "each night", "once per game", "if you",
                "when you", "navigation", "jump to", "edit", "main page"
            ]):
                continue
            # Return first good match
            if len(flavor) >= 20:
                return flavor
    
    return None


def fetch_flavor_from_wiki(char_name: str) -> str | None:
    """Fetch flavor text from the BOTC wiki for a character.
    
    Args:
        char_name: Character name (used in wiki URL)
    
    Returns:
        Flavor text or None if not found
    """
    # Construct wiki URL (spaces become underscores)
    wiki_name = char_name.replace(" ", "_")
    url = f"{WIKI_BASE_URL}/{wiki_name}"
    
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
    
    print(f"Loaded {len(previous_data)} characters from previous data")
    print("Checking flavor text updates...")
    
    for char_id, character in characters.items():
        char_name = character.get("name", char_id)
        
        # Check if update is needed
        if not force and not needs_flavor_update(character, previous_data):
            # Preserve existing flavor
            if preserve_flavor_text(character, previous_data):
                stats["preserved"] += 1
            else:
                stats["skipped"] += 1
            continue
        
        # Need to fetch flavor
        print(f"  Fetching: {char_name}...", end=" ", flush=True)
        
        flavor = fetch_flavor_from_wiki(char_name)
        
        if flavor:
            character["flavor"] = flavor
            stats["fetched"] += 1
            print(f"✓ ({len(flavor)} chars)")
        else:
            # Try to preserve previous flavor on failure
            if preserve_flavor_text(character, previous_data):
                stats["failed"] += 1
                print(f"✗ (preserved previous)")
            else:
                character["flavor"] = ""
                stats["failed"] += 1
                print(f"✗ (no flavor)")
        
        # Rate limiting - be nice to the wiki server
        time.sleep(RATE_LIMIT_SECONDS)
    
    print(f"\nFlavor text summary:")
    print(f"  Fetched: {stats['fetched']}")
    print(f"  Preserved: {stats['preserved']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Skipped: {stats['skipped']}")
    
    return stats


def save_updated_characters(characters: dict[str, dict]) -> None:
    """Save characters with updated flavor text back to files."""
    for char_id, character in characters.items():
        edition = character.get("edition", "unknown")
        edition_dir = CHARACTERS_DIR / edition
        edition_dir.mkdir(parents=True, exist_ok=True)
        
        char_file = edition_dir / f"{char_id}.json"
        with open(char_file, "w", encoding="utf-8") as f:
            json.dump(character, f, indent=2, ensure_ascii=False)
    
    # Update combined file
    all_chars = list(characters.values())
    all_file = CHARACTERS_DIR / "all_characters.json"
    with open(all_file, "w", encoding="utf-8") as f:
        json.dump(all_chars, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(characters)} characters with flavor text")


def load_scraped_characters() -> dict[str, dict]:
    """Load characters from the combined all_characters.json file."""
    all_file = CHARACTERS_DIR / "all_characters.json"
    
    if not all_file.exists():
        raise FileNotFoundError(f"Character data not found at {all_file}. Run character_scraper.py first.")
    
    with open(all_file, "r", encoding="utf-8") as f:
        characters_list = json.load(f)
    
    return {char["id"]: char for char in characters_list}


def main():
    """Main entry point for standalone flavor fetching."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch flavor text for BOTC characters")
    parser.add_argument("--force", action="store_true", help="Force fetch all flavor texts")
    args = parser.parse_args()
    
    # Load scraped character data
    print("Loading character data...")
    characters = load_scraped_characters()
    print(f"Loaded {len(characters)} characters")
    
    # Update flavor text
    print("\n--- Updating flavor text ---")
    stats = update_flavor_for_characters(characters, force=args.force)
    
    # Save if any fetches were made
    if stats["fetched"] > 0:
        print("\n--- Saving updated characters ---")
        save_updated_characters(characters)
    else:
        print("\nNo new flavor text fetched, skipping save.")
    
    print("\n✓ Flavor text update complete!")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
