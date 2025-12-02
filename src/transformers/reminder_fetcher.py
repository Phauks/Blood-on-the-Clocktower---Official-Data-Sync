"""
Blood on the Clocktower - Reminder Token Fetcher

Fetches reminder tokens from the BOTC wiki "How to Run" sections.
The official script tool doesn't expose reminder tokens for all characters,
so we extract them from wiki documentation.

Token extraction strategy:
1. Fetch wiki page for character
2. Extract "How to Run" section
3. Use regex to find ALL CAPS tokens followed by "reminder"
4. Filter out info tokens (YOU ARE, THESE ARE YOUR MINIONS, etc.)
5. Apply manual overrides for known edge cases (token counts, etc.)

Incremental update logic (same as flavor_fetcher):
- Only fetches when: new character, ability changed, or reminders not yet fetched
- Preserves existing reminders from previous data when no update needed
"""

import json
import re
import time
import urllib.parse
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from tqdm import tqdm

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scrapers"))
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

# Import from config (consolidated constants)
from config import (
    WIKI_BASE_URL,
    CHARACTERS_DIR,
    RATE_LIMIT_SECONDS,
    USER_AGENT,
)

# Import shared utilities
from http_client import fetch_with_retry
from data_loader import load_previous_character_data

# Info tokens to exclude (not reminder tokens)
INFO_TOKEN_EXCLUSIONS = [
    "YOU ARE",
    "THIS PLAYER IS",
    "THESE ARE YOUR MINIONS",
    "THIS IS THE DEMON",
    "THESE CHARACTERS ARE NOT IN PLAY",
    "THIS CHARACTER SELECTED YOU",
    "DID YOU NOMINATE TODAY",
    "DID YOU VOTE TODAY"
]

# Manual overrides for known edge cases (use sparingly - prefer improving logic)
# Key: character_id, Value: list of reminder tokens (duplicates = multiple tokens)
TOKEN_OVERRIDES = {
    # Lunatic needs 3 CHOSEN tokens (max for Po scenario)
    "lunatic": ["CHOSEN", "CHOSEN", "CHOSEN"],
    # Po: 3 ATTACKS token + 3 DEAD for triple kill (charging mechanic)
    "po": ["3 ATTACKS", "DEAD", "DEAD", "DEAD"],
    # Juggler: Up to 5 correct guesses
    "juggler": ["CORRECT", "CORRECT", "CORRECT", "CORRECT", "CORRECT"],
    # Zenomancer: "One or more players" can have GOAL
    "zenomancer": ["GOAL", "GOAL", "GOAL"],
    # Al-Hadikhia: Single-digit tokens (unique format)
    "alhadikhia": ["1", "2", "3"],
    # Leviathan: Day tracking (comma-separated in wiki, not all detected)
    "leviathan": ["DAY 1", "DAY 2", "DAY 3", "DAY 4", "DAY 5", "GOOD PLAYER EXECUTED"],
    # Ojo: Wiki error - uses lowercase/unemphasized "Dead" instead of "DEAD"
    "ojo": ["DEAD"],
    # Yaggababble: Can kill multiple players per day
    "yaggababble": ["DEAD", "DEAD", "DEAD"],
}


def needs_reminder_update(character: dict, previous_data: dict[str, dict]) -> bool:
    """Determine if we need to fetch reminders for this character.
    
    Args:
        character: Current character object (just scraped)
        previous_data: Character data from previous run
    
    Returns:
        bool: True if reminder fetch is needed
    
    Note: We track whether reminders have been fetched via _remindersFetched flag.
          Empty [] is valid - not all characters have reminder tokens.
    """
    char_id = character.get("id")
    if not char_id:
        return True
    
    # Case 1: New character (not in previous data)
    if char_id not in previous_data:
        return True
    
    previous = previous_data[char_id]
    
    # Case 2: Reminders not yet fetched (check flag)
    if not previous.get("_remindersFetched", False):
        return True
    
    # Case 3: Character ability changed (might have new reminders)
    if character.get("ability", "") != previous.get("ability", ""):
        return True
    
    # Case 4: Character name changed (wiki URL would change)
    if character.get("name", "") != previous.get("name", ""):
        return True
    
    # Otherwise, no update needed
    return False


def preserve_reminders(character: dict, previous_data: dict[str, dict]) -> bool:
    """Copy reminders from previous data if available.
    
    Args:
        character: Current character object to update
        previous_data: Character data from previous run
    
    Returns:
        bool: True if reminders were preserved
    """
    char_id = character.get("id")
    if not char_id or char_id not in previous_data:
        return False
    
    previous = previous_data[char_id]
    
    # Only preserve if reminders were previously fetched
    if previous.get("_remindersFetched", False):
        character["reminders"] = previous.get("reminders", [])
        character["remindersGlobal"] = previous.get("remindersGlobal", [])
        character["_remindersFetched"] = True
        return True
    
    return False


def fetch_wiki_page(char_name: str) -> str | None:
    """Fetch a character's wiki page HTML with retry logic.
    
    Args:
        char_name: Character name (spaces will be replaced with underscores)
    
    Returns:
        HTML content or None if request failed
    """
    # Replace spaces with underscores, then URL-encode special characters
    wiki_name = char_name.replace(" ", "_")
    # URL-encode special characters (apostrophes, etc.) but keep underscores
    wiki_name = urllib.parse.quote(wiki_name, safe="_")
    url = f"{WIKI_BASE_URL}/{wiki_name}"
    
    # Use shared HTTP client with retry logic
    response = fetch_with_retry(
        url,
        on_retry=lambda attempt, e: tqdm.write(f"    Retry {attempt} for {char_name}: {e}")
    )
    
    if response:
        return response.text
    else:
        tqdm.write(f"    Request failed for {char_name} after retries")
        return None


def extract_how_to_run_section(html: str) -> str | None:
    """Extract the 'How to Run' section text from a wiki page.
    
    Args:
        html: Raw HTML content from wiki page
    
    Returns:
        Text content of "How to Run" section, or None if not found
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find the "How to Run" heading (could be h2 or h3)
    how_to_run_heading = None
    for heading in soup.find_all(['h2', 'h3']):
        heading_text = heading.get_text().strip().upper()
        if 'HOW TO RUN' in heading_text:
            how_to_run_heading = heading
            break
    
    if not how_to_run_heading:
        return None
    
    # Collect all content until the next heading of same or higher level
    content_parts = []
    heading_level = int(how_to_run_heading.name[1])  # e.g., 'h2' -> 2
    
    for sibling in how_to_run_heading.find_next_siblings():
        # Stop at next heading of same or higher level
        if sibling.name in ['h1', 'h2', 'h3']:
            sibling_level = int(sibling.name[1])
            if sibling_level <= heading_level:
                break
        
        # Get text content
        text = sibling.get_text(separator=' ', strip=True)
        if text:
            content_parts.append(text)
    
    return ' '.join(content_parts) if content_parts else None


def extract_tokens_from_text(text: str, char_name: str = "") -> list[str]:
    """Extract reminder token names from "How to Run" text.
    
    Args:
        text: Text content from "How to Run" section
        char_name: Character name (to distinguish own tokens from others)
    
    Returns:
        List of token names (may contain duplicates for multiple tokens)
    """
    tokens = []
    
    # Normalize character name for matching
    char_name_lower = char_name.lower().replace(" ", "").replace("-", "")
    
    # First, identify tokens that belong to OTHER characters
    # Pattern: "the Demon's DEAD reminder" or "the Imp's DEAD reminder"
    # But NOT "the Drunk's IS THE DRUNK reminder" (same character)
    # Include digits for tokens like "NIGHT 1", "DAY 3", etc.
    other_char_token_pattern = r"the\s+(\w+)'s\s+([A-Z0-9][A-Z0-9\s:]*[A-Z0-9]|[A-Z]{2,})\s+reminder"
    other_char_tokens = set()
    for match in re.finditer(other_char_token_pattern, text):
        owner_name = match.group(1).lower()
        token_name = match.group(2).strip().upper()
        # Only exclude if the owner is a DIFFERENT character
        if owner_name != char_name_lower and owner_name not in char_name_lower:
            other_char_tokens.add(token_name)
    
    # Pattern 1: "the X reminder token" or "X reminder"
    # Captures ALL CAPS words/phrases before "reminder"
    # Match multi-word tokens OR single uppercase words (2+ chars)
    # Include colons for tokens like "FINAL NIGHT: NO ATTACK"
    # Include digits for tokens like "NIGHT 1", "DAY 3", etc.
    pattern1 = r'\b([A-Z0-9][A-Z0-9\s:\']*[A-Z0-9]|[A-Z]{2,})\s+reminder(?:\s+token)?'
    
    # Pattern 2: "marked X" or "mark them with the X"
    pattern2 = r'(?:marked?(?:\s+them)?(?:\s+with)?(?:\s+the)?)\s+([A-Z0-9][A-Z0-9\s:\']*[A-Z0-9]|[A-Z]{2,})'
    
    # Pattern 3: "put the X reminder" (common phrasing)
    pattern3 = r'put\s+(?:the\s+)?(?:\w+\'s\s+)?([A-Z0-9][A-Z0-9\s:\']*[A-Z0-9]|[A-Z]{2,})\s+reminder'
    
    # Find all matches
    for pattern in [pattern1, pattern2, pattern3]:
        matches = re.findall(pattern, text)
        for match in matches:
            token = match.strip().upper()
            # Clean up any possessive artifacts
            token = re.sub(r"'S$", "", token)
            tokens.append(token)
    
    # Remove duplicates while preserving first occurrence order
    seen = set()
    unique_tokens = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            unique_tokens.append(token)
    
    # Filter out info tokens and tokens belonging to other characters
    filtered_tokens = []
    for token in unique_tokens:
        # Check if token matches or contains an info token phrase
        # Note: We check if exclusion is IN token (e.g., "YOU ARE" in "YOU ARE THE DEMON")
        # NOT if token is in exclusion (e.g., "MINION" in "THESE ARE YOUR MINIONS")
        is_info_token = any(
            token == excl or excl in token
            for excl in INFO_TOKEN_EXCLUSIONS
        )
        # Filter tokens that were referenced as belonging to other characters
        is_other_char_token = token in other_char_tokens
        
        if not is_info_token and not is_other_char_token:
            filtered_tokens.append(token)
    
    return filtered_tokens


def infer_token_count(text: str, token: str) -> int:
    """Infer how many of a token are needed based on wiki text.
    
    Args:
        text: "How to Run" section text
        token: Token name to check
    
    Returns:
        Number of tokens needed (default 1)
    """
    # Check for specific number patterns first
    # "Mark the two chosen players with SAFE reminders" -> 2
    # "mark two of them with a VISITOR reminder" -> 2
    # "three players" -> 3
    number_words = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        '1': 1, '2': 2, '3': 3, '4': 4, '5': 5
    }
    
    # Pattern: "the two/three/etc players with {TOKEN} reminders"
    for word, count in number_words.items():
        pattern = rf'{word}\s+(?:chosen\s+)?players?\s+with\s+(?:a\s+)?{token}\s+reminders?'
        if re.search(pattern, text, re.IGNORECASE):
            return count
    
    # Pattern: "mark two/three of them with a {TOKEN} reminder"
    for word, count in number_words.items():
        pattern = rf'(?:mark\s+)?{word}\s+of\s+them\s+with\s+(?:a\s+)?{token}\s+reminder'
        if re.search(pattern, text, re.IGNORECASE):
            return count
    
    # Check for "each player" patterns (default to 3 for demon scenarios)
    each_player_patterns = [
        rf'{token}\s+reminder(?:s)?\s+on\s+each\s+player',
        rf'put\s+(?:a\s+)?{token}\s+reminder\s+on\s+each',
    ]
    
    for pattern in each_player_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return 3
    
    # Explicit plural without number (default to 2)
    if re.search(rf'{token}\s+reminders\b', text, re.IGNORECASE):
        return 2
    
    return 1


def get_reminders_for_character(char_id: str, char_name: str, verbose: int = 0) -> list[str]:
    """Get reminder tokens for a character from wiki.
    
    Args:
        char_id: Character ID (for override lookup)
        char_name: Character name (for wiki URL)
        verbose: Verbosity level (0=quiet, 1=basic, 2+=debug)
    
    Returns:
        List of reminder tokens
    """
    # Check for manual override first
    if char_id in TOKEN_OVERRIDES:
        if verbose >= 2:
            tqdm.write(f"    [override] Using manual override for {char_name}")
        return TOKEN_OVERRIDES[char_id].copy()
    
    # Fetch wiki page
    html = fetch_wiki_page(char_name)
    if not html:
        return []
    
    # Extract "How to Run" section
    how_to_run = extract_how_to_run_section(html)
    if not how_to_run:
        if verbose >= 1:
            tqdm.write(f"    No 'How to Run' section found for {char_name}")
        return []
    
    # Extract tokens (pass char_name to distinguish own tokens from others)
    tokens = extract_tokens_from_text(how_to_run, char_name)
    
    # Expand tokens based on count inference
    expanded_tokens = []
    for token in tokens:
        count = infer_token_count(how_to_run, token)
        expanded_tokens.extend([token] * count)
    
    return expanded_tokens


def fetch_reminders_for_edition(
    edition: str,
    dry_run: bool = False,
    team_filter: str | None = None,
    verbose: int = 0,
    show_progress: bool = True,
    incremental: bool = False,
    previous_data: dict[str, dict] | None = None
) -> dict[str, list[str]]:
    """Fetch reminder tokens for all characters in an edition.
    
    Args:
        edition: Edition folder name (e.g., "tb", "bmr")
        dry_run: If True, print what would be fetched without making requests
        team_filter: Optional team to filter by (e.g., "townsfolk", "demon")
        verbose: Verbosity level (0=quiet, 1=basic, 2+=debug)
        show_progress: If True, show progress bar
        incremental: If True, only fetch for new/changed characters
        previous_data: Pre-loaded previous character data (for incremental mode)
    
    Returns:
        Dict mapping character_id to list of reminder tokens
    """
    edition_dir = CHARACTERS_DIR / edition
    if not edition_dir.exists():
        print(f"Edition directory not found: {edition_dir}")
        return {}
    
    # Load previous data if incremental mode and not already provided
    if incremental and previous_data is None:
        previous_data = load_previous_character_data()
    
    results = {}
    char_files = sorted(edition_dir.glob("*.json"))
    
    # Filter by team if specified
    if team_filter:
        filtered_files = []
        for char_file in char_files:
            try:
                with open(char_file, "r", encoding="utf-8") as f:
                    char_data = json.load(f)
                if char_data.get("team", "").lower() == team_filter.lower():
                    filtered_files.append(char_file)
            except Exception:
                pass
        char_files = filtered_files
    
    filter_msg = f" (team: {team_filter})" if team_filter else ""
    
    # Track stats for incremental mode
    skipped_count = 0
    preserved_count = 0
    fetched_count = 0
    
    # Use progress bar or verbose output
    if show_progress and not verbose:
        pbar = tqdm(char_files, desc=f"{edition}{filter_msg}", unit="char")
    else:
        pbar = char_files
        if verbose >= 1:
            mode_msg = " (incremental)" if incremental else ""
            print(f"\nFetching reminders for {len(char_files)} characters in '{edition}'{filter_msg}{mode_msg}...")
    
    for char_file in pbar:
        try:
            with open(char_file, "r", encoding="utf-8") as f:
                character = json.load(f)
        except Exception as e:
            if verbose >= 1:
                tqdm.write(f"  Error loading {char_file.name}: {e}")
            continue
        
        char_id = character.get("id", char_file.stem)
        char_name = character.get("name", char_id)
        
        if dry_run:
            if verbose >= 1:
                tqdm.write(f"  {char_name}... (dry run)")
            results[char_id] = ["DRY_RUN"]
            continue
        
        # Incremental mode: check if update needed
        if incremental and previous_data:
            if not needs_reminder_update(character, previous_data):
                # Preserve existing reminders
                if preserve_reminders(character, previous_data):
                    results[char_id] = character.get("reminders", [])
                    preserved_count += 1
                    if verbose >= 2:
                        tqdm.write(f"  {char_name} -> (preserved: {results[char_id]})")
                else:
                    skipped_count += 1
                    if verbose >= 2:
                        tqdm.write(f"  {char_name} -> (skipped, no changes)")
                continue
        
        # Fetch reminders from wiki
        reminders = get_reminders_for_character(char_id, char_name, verbose=verbose)
        results[char_id] = reminders
        fetched_count += 1
        
        if verbose >= 1:
            if reminders:
                tqdm.write(f"  {char_name} -> {reminders}")
            else:
                tqdm.write(f"  {char_name} -> (no tokens found)")
        
        # Rate limiting (only when actually fetching)
        time.sleep(RATE_LIMIT_SECONDS)
    
    # Print incremental stats
    if incremental and verbose >= 1:
        tqdm.write(f"  [Stats] Fetched: {fetched_count}, Preserved: {preserved_count}, Skipped: {skipped_count}")
    
    return results


def update_character_files_with_reminders(edition: str, reminders: dict[str, list[str]]) -> None:
    """Update character JSON files with fetched reminder tokens.
    
    Args:
        edition: Edition folder name
        reminders: Dict mapping character_id to reminder token list
    """
    edition_dir = CHARACTERS_DIR / edition
    
    for char_file in edition_dir.glob("*.json"):
        char_id = char_file.stem
        
        if char_id not in reminders:
            continue
        
        try:
            with open(char_file, "r", encoding="utf-8") as f:
                character = json.load(f)
            
            # Update reminders (empty array is valid - not all characters have tokens)
            character["reminders"] = reminders[char_id]
            
            # Set remindersGlobal to empty array
            character["remindersGlobal"] = []
            
            # Mark that reminders have been fetched (for incremental mode)
            character["_remindersFetched"] = True
            
            # Write back
            with open(char_file, "w", encoding="utf-8") as f:
                json.dump(character, f, indent=2, ensure_ascii=False)
                f.write("\n")
            
        except Exception as e:
            print(f"Error updating {char_file.name}: {e}")


def fetch_single_character(char_id: str, char_name: str) -> None:
    """Fetch and display reminders for a single character.
    
    Args:
        char_id: Character ID
        char_name: Character display name
    """
    print(f"Fetching reminders for '{char_name}' (id: {char_id})...")
    reminders = get_reminders_for_character(char_id, char_name)
    if reminders:
        print(f"  Reminders: {reminders}")
    else:
        print("  No reminders found")


def get_all_editions() -> list[str]:
    """Get list of all edition folder names."""
    editions = []
    for item in CHARACTERS_DIR.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            editions.append(item.name)
    return sorted(editions)


def main():
    """Main entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fetch reminder tokens from BOTC wiki"
    )
    parser.add_argument(
        "--edition", "-e",
        help="Edition to fetch (default: all editions if --team specified, else 'tb')"
    )
    parser.add_argument(
        "--character", "-c",
        help="Fetch single character by name (e.g., 'Imp', 'Scarlet Woman')"
    )
    parser.add_argument(
        "--team", "-t",
        choices=["townsfolk", "outsider", "minion", "demon", "traveller", "fabled"],
        help="Filter by team type (searches all editions if --edition not specified)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be fetched without making requests"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update character JSON files with fetched reminders"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="count",
        default=0,
        help="Increase output verbosity (-v for basic, -vv for debug)"
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar (useful for logging)"
    )
    parser.add_argument(
        "--incremental", "-i",
        action="store_true",
        help="Only fetch for new/changed characters (default when called from main scraper)"
    )
    parser.add_argument(
        "--force-all",
        action="store_true",
        help="Force fetch all characters, ignoring incremental logic"
    )
    
    args = parser.parse_args()
    
    # Single character mode
    if args.character:
        char_id = args.character.lower().replace(" ", "").replace("'", "").replace("-", "")
        fetch_single_character(char_id, args.character)
        return
    
    # Determine editions to process
    if args.edition:
        editions = [args.edition]
    elif args.team:
        # If team specified but no edition, search all editions
        editions = get_all_editions()
    else:
        # Default to tb
        editions = ["tb"]
    
    # Fetch reminders across all specified editions
    all_reminders = {}
    show_progress = not args.no_progress and not args.verbose
    
    # Determine incremental mode (--force-all overrides --incremental)
    use_incremental = args.incremental and not args.force_all
    
    # Pre-load previous data once if incremental
    previous_data = load_previous_character_data() if use_incremental else None
    
    for edition in editions:
        reminders = fetch_reminders_for_edition(
            edition,
            dry_run=args.dry_run,
            team_filter=args.team,
            verbose=args.verbose,
            show_progress=show_progress,
            incremental=use_incremental,
            previous_data=previous_data
        )
        all_reminders.update(reminders)
        
        # Update files if requested (per edition)
        if args.update and not args.dry_run and reminders:
            update_character_files_with_reminders(edition, reminders)
    
    # Summary
    print(f"\n=== Summary ===")
    total = len(all_reminders)
    with_tokens = sum(1 for r in all_reminders.values() if r)
    print(f"Characters processed: {total}")
    print(f"Characters with tokens: {with_tokens}")
    print(f"Characters without tokens: {total - with_tokens}")
    
    if args.update and not args.dry_run:
        print("Files updated!")


if __name__ == "__main__":
    main()
