"""
Writer functions for Blood on the Clocktower scraper.

Functions for saving character data to JSON files and creating manifests.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

# Handle both direct script execution and module import
try:
    from .config import CHARACTERS_DIR, DATA_DIR, SCRIPT_TOOL_URL
except ImportError:
    from config import CHARACTERS_DIR, DATA_DIR, SCRIPT_TOOL_URL

# Schema version - increment when breaking changes are made to data format
SCHEMA_VERSION = 1

# Internal fields to strip when saving (except _remindersFetched which needs to persist)
INTERNAL_FIELDS_TO_STRIP = {"_imageUrl"}


def strip_internal_fields(char: dict, preserve_reminder_flag: bool = True) -> dict:
    """Create a copy of character dict with internal fields removed.
    
    Internal fields are prefixed with underscore (e.g., _imageUrl).
    The _remindersFetched flag is optionally preserved for incremental updates.
    
    Args:
        char: Character dict (may contain internal fields)
        preserve_reminder_flag: If True, keep _remindersFetched field
    
    Returns:
        New dict with internal fields removed
    """
    result = {}
    for k, v in char.items():
        if k.startswith("_"):
            # Optionally preserve _remindersFetched
            if preserve_reminder_flag and k == "_remindersFetched":
                result[k] = v
            # Skip other internal fields
            continue
        result[k] = v
    return result


def save_characters_by_edition(characters: dict, output_dir: Path | None = None) -> None:
    """Save characters to individual JSON files organized by edition.
    
    Preserves _remindersFetched flag from existing files for incremental updates.
    Other internal fields (like _imageUrl) are stripped before saving.
    
    Args:
        characters: Character data dict
        output_dir: Override output directory (defaults to CHARACTERS_DIR)
    """
    char_dir = output_dir or CHARACTERS_DIR
    
    # Group characters by edition
    by_edition: dict[str, list[dict]] = {}
    
    for char in characters.values():
        edition = char["edition"]
        if edition not in by_edition:
            by_edition[edition] = []
        by_edition[edition].append(char)
    
    # Save each edition (alphabetically)
    for edition in sorted(by_edition.keys()):
        chars = by_edition[edition]
        edition_dir = char_dir / edition
        edition_dir.mkdir(parents=True, exist_ok=True)
        
        # Save individual character files
        for char in chars:
            char_file = edition_dir / f"{char['id']}.json"
            
            # Preserve _remindersFetched and reminders from existing file
            if char_file.exists():
                try:
                    with open(char_file, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                    # Preserve reminder data if it was previously fetched
                    if existing.get("_remindersFetched", False):
                        char["_remindersFetched"] = True
                        char["reminders"] = existing.get("reminders", [])
                        char["remindersGlobal"] = existing.get("remindersGlobal", [])
                except (json.JSONDecodeError, IOError):
                    pass
            
            # Individual files preserve _remindersFetched for incremental updates
            clean_char = strip_internal_fields(char, preserve_reminder_flag=True)
            with open(char_file, "w", encoding="utf-8") as f:
                json.dump(clean_char, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(chars)} characters to {edition_dir}")
    
    # Save combined file (strip ALL internal fields for distribution)
    all_chars = [strip_internal_fields(char, preserve_reminder_flag=False) for char in characters.values()]
    all_file = char_dir / "all_characters.json"
    with open(all_file, "w", encoding="utf-8") as f:
        json.dump(all_chars, f, indent=2, ensure_ascii=False)
    print(f"Saved combined file with {len(all_chars)} characters to {all_file}")


def create_manifest(characters: dict, output_dir: Path | None = None) -> dict:
    """Create manifest.json with version info and character index.
    
    Includes schemaVersion for breaking changes and contentHash for integrity.
    
    Args:
        characters: Character data dict
        output_dir: Override output directory (defaults to DATA_DIR)
    
    Returns:
        The manifest dict
    """
    data_dir = output_dir or DATA_DIR
    
    editions = {}
    for char in characters.values():
        edition = char["edition"]
        if edition not in editions:
            editions[edition] = []
        editions[edition].append(char["id"])
    
    # Sort editions alphabetically and character IDs within each edition
    editions = {k: sorted(v) for k, v in sorted(editions.items())}
    
    # Compute content hash from character data (for integrity checking)
    # Strip internal fields before hashing to match what gets saved
    all_chars = [strip_internal_fields(char) for char in characters.values()]
    char_json = json.dumps(all_chars, sort_keys=True, ensure_ascii=False)
    content_hash = hashlib.sha256(char_json.encode()).hexdigest()[:16]
    
    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "version": datetime.now(timezone.utc).strftime("%Y.%m.%d"),
        "generated": datetime.now(timezone.utc).isoformat(),
        "contentHash": content_hash,
        "source": SCRIPT_TOOL_URL,
        "total_characters": len(characters),
        "editions": editions,
        "edition_counts": {k: len(v) for k, v in editions.items()},
    }
    
    manifest_file = data_dir / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Saved manifest to {manifest_file}")
    
    return manifest
