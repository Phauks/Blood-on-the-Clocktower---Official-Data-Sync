"""
Data loading utilities for Blood on the Clocktower character data.

Provides shared functions for loading character JSON files,
used by multiple modules (reminder_fetcher, flavor_fetcher, etc.).
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import config - handle both module and direct execution
try:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent / "scrapers"))
    from config import CHARACTERS_DIR
except ImportError:
    # Fallback
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    CHARACTERS_DIR = PROJECT_ROOT / "data" / "characters"


def load_previous_character_data(
    characters_dir: Optional[Path] = None,
) -> Dict[str, Dict[str, Any]]:
    """Load all existing character JSON files from data/characters/*/*.json.

    Args:
        characters_dir: Path to characters directory (default: from config)

    Returns:
        Dictionary mapping character IDs to character data dictionaries
    """
    if characters_dir is None:
        characters_dir = CHARACTERS_DIR

    previous_data = {}

    if not characters_dir.exists():
        return previous_data

    # Search all character files (skip all_characters.json)
    for char_file in characters_dir.glob("**/*.json"):
        if char_file.name == "all_characters.json":
            continue

        try:
            with open(char_file, "r", encoding="utf-8") as f:
                character = json.load(f)
                char_id = character.get("id")
                if char_id:
                    previous_data[char_id] = character
        except Exception as e:
            print(f"Warning: Could not load {char_file}: {e}")

    return previous_data


def load_character_file(char_file: Path) -> Optional[Dict[str, Any]]:
    """Load a single character JSON file.

    Args:
        char_file: Path to character JSON file

    Returns:
        Character dictionary or None if loading failed
    """
    try:
        with open(char_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_character_file(char_file: Path, character: Dict[str, Any]) -> bool:
    """Save a character dictionary to JSON file.

    Args:
        char_file: Path to save to
        character: Character data dictionary

    Returns:
        True if successful, False on error
    """
    try:
        # Ensure parent directory exists
        char_file.parent.mkdir(parents=True, exist_ok=True)

        with open(char_file, "w", encoding="utf-8") as f:
            json.dump(character, f, indent=2, ensure_ascii=False)
            f.write("\n")
        return True
    except Exception as e:
        print(f"Error saving {char_file}: {e}")
        return False


def get_character_files_by_edition(
    edition: str, characters_dir: Optional[Path] = None
) -> List[Path]:
    """Get all character JSON files for an edition.

    Args:
        edition: Edition folder name (e.g., "tb", "bmr")
        characters_dir: Path to characters directory (default: from config)

    Returns:
        Sorted list of Path objects for character files in the edition
    """
    if characters_dir is None:
        characters_dir = CHARACTERS_DIR

    edition_dir = characters_dir / edition
    if not edition_dir.exists():
        return []

    return sorted(edition_dir.glob("*.json"))
