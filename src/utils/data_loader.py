"""
Data loading utilities for Blood on the Clocktower character data.

Provides shared functions for loading character JSON files,
used by multiple modules (reminder_fetcher, flavor_fetcher, etc.).
"""

import json
from pathlib import Path
from typing import Any

from src.scrapers.config import CHARACTERS_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_previous_character_data(
    characters_dir: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Load all existing character JSON files from data/characters/*/*.json.

    Args:
        characters_dir: Path to characters directory (default: from config)

    Returns:
        Dictionary mapping character IDs to character data dictionaries
    """
    if characters_dir is None:
        characters_dir = CHARACTERS_DIR

    previous_data: dict[str, dict[str, Any]] = {}

    if not characters_dir.exists():
        return previous_data

    # Search all character files (skip all_characters.json)
    for char_file in characters_dir.glob("**/*.json"):
        if char_file.name == "all_characters.json":
            continue

        try:
            with open(char_file, encoding="utf-8") as f:
                character = json.load(f)
                char_id = character.get("id")
                if char_id:
                    previous_data[char_id] = character
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not load {char_file}: {e}")

    return previous_data


def load_character_file(char_file: Path) -> dict[str, Any] | None:
    """Load a single character JSON file.

    Args:
        char_file: Path to character JSON file

    Returns:
        Character dictionary or None if loading failed
    """
    try:
        with open(char_file, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
            return data
    except (json.JSONDecodeError, OSError):
        return None


def save_character_file(char_file: Path, character: dict[str, Any]) -> bool:
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
    except (OSError, TypeError) as e:
        logger.error(f"Error saving {char_file}: {e}")
        return False


def get_character_files_by_edition(edition: str, characters_dir: Path | None = None) -> list[Path]:
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
