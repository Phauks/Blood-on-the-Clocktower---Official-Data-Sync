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

# Canonical field order for character JSON files
FIELD_ORDER = [
    "id",
    "name", 
    "edition",
    "team",
    "firstNightReminder",
    "otherNightReminder",
    "reminders",
    "remindersGlobal",
    "setup",
    "ability",
    "flavor",
    "image",
    "firstNight",
    "otherNight",
    "jinxes",
    # Internal fields at end
    "_remindersFetched",
]


def order_character_fields(char: dict) -> dict:
    """Order character fields in canonical order.
    
    Args:
        char: Character dict with fields in any order
    
    Returns:
        New dict with fields in FIELD_ORDER
    """
    ordered = {}
    
    # Add fields in canonical order
    for field in FIELD_ORDER:
        if field in char:
            ordered[field] = char[field]
    
    # Add any remaining fields not in FIELD_ORDER (shouldn't happen normally)
    for field in char:
        if field not in ordered:
            ordered[field] = char[field]
    
    return ordered


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
            
            # Preserve _remindersFetched, reminders, and flavor from existing file
            if char_file.exists():
                try:
                    with open(char_file, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                    # Preserve reminder data if it was previously fetched
                    if existing.get("_remindersFetched", False):
                        char["_remindersFetched"] = True
                        char["reminders"] = existing.get("reminders", [])
                        char["remindersGlobal"] = existing.get("remindersGlobal", [])
                    # Preserve flavor text if it exists
                    if existing.get("flavor"):
                        char["flavor"] = existing["flavor"]
                except (json.JSONDecodeError, IOError):
                    pass
            
            # Ensure flavor field exists (empty string if not set)
            if "flavor" not in char:
                char["flavor"] = ""
            
            # Strip internal fields, order fields, and save
            clean_char = strip_internal_fields(char, preserve_reminder_flag=True)
            ordered_char = order_character_fields(clean_char)
            with open(char_file, "w", encoding="utf-8") as f:
                json.dump(ordered_char, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(chars)} characters to {edition_dir}")
    
    # Save combined file (strip ALL internal fields, order fields for distribution)
    all_chars = []
    for char in characters.values():
        # Ensure flavor field exists
        if "flavor" not in char:
            char["flavor"] = ""
        clean_char = strip_internal_fields(char, preserve_reminder_flag=False)
        ordered_char = order_character_fields(clean_char)
        all_chars.append(ordered_char)
    
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
    edition_reminders = {}  # Track reminder counts per edition
    total_reminders = 0
    total_jinxes = 0
    total_flavor = 0
    
    for char in characters.values():
        edition = char["edition"]
        if edition not in editions:
            editions[edition] = []
            edition_reminders[edition] = 0
        editions[edition].append(char["id"])
        
        # Count reminders
        char_reminders = len(char.get("reminders", []))
        edition_reminders[edition] += char_reminders
        total_reminders += char_reminders
        
        # Count jinxes (each jinx stored bidirectionally, so divide by 2 at end)
        total_jinxes += len(char.get("jinxes", []))
        
        # Count characters with flavor text
        if char.get("flavor"):
            total_flavor += 1
    
    # Jinxes are stored on both characters, so divide by 2
    total_jinxes = total_jinxes // 2
    
    # Sort editions alphabetically and character IDs within each edition
    editions = {k: sorted(v) for k, v in sorted(editions.items())}
    edition_reminders = {k: v for k, v in sorted(edition_reminders.items())}
    
    # Compute content hash from character data (for integrity checking)
    # Strip internal fields before hashing to match what gets saved
    all_chars = [strip_internal_fields(char) for char in characters.values()]
    char_json = json.dumps(all_chars, sort_keys=True, ensure_ascii=False)
    content_hash = hashlib.sha256(char_json.encode()).hexdigest()[:16]
    
    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "version": datetime.now(timezone.utc).strftime("%Y.%m.%d"),
        "generated": datetime.now(timezone.utc).isoformat(),
        "lastModified": datetime.now(timezone.utc).isoformat(),
        "contentHash": content_hash,
        "source": SCRIPT_TOOL_URL,
        "total_characters": len(characters),
        "total_reminders": total_reminders,
        "total_jinxes": total_jinxes,
        "total_flavor": total_flavor,
        "editions": editions,
        "edition_counts": {k: len(v) for k, v in editions.items()},
        "edition_reminders": edition_reminders,
    }
    
    manifest_file = data_dir / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Saved manifest to {manifest_file}")
    
    return manifest
