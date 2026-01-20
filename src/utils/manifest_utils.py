"""
Shared manifest utilities for Blood on the Clocktower data sync.

Provides common functions for computing manifest statistics and creating manifest files.
"""

import hashlib
import json
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.scrapers.config import SCHEMA_VERSION, SCRIPT_TOOL_URL


def strip_internal_fields_for_hash(char: dict) -> dict:
    """Remove internal fields (prefixed with _) for content hash computation.

    Args:
        char: Character dict

    Returns:
        New dict with internal fields removed
    """
    return {k: v for k, v in char.items() if not k.startswith("_")}


def compute_manifest_stats(characters: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Compute statistics for manifest from character data.

    Args:
        characters: Iterable of character dicts

    Returns:
        Dict containing computed stats:
        - editions: Dict mapping edition to list of character IDs
        - edition_counts: Dict mapping edition to character count
        - edition_reminders: Dict mapping edition to reminder count
        - total_characters: Total number of characters
        - total_reminders: Total number of reminder tokens
        - total_jinxes: Total number of jinx pairs
        - total_flavor: Number of characters with flavor text
        - content_hash: SHA256 hash of character data
    """
    editions: dict[str, list[str]] = {}
    edition_reminders: dict[str, int] = {}
    total_reminders = 0
    total_jinxes = 0
    total_flavor = 0
    all_chars_for_hash = []

    for char in characters:
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

        # Collect for hash computation
        all_chars_for_hash.append(strip_internal_fields_for_hash(char))

    # Jinxes are stored on both characters, so divide by 2
    total_jinxes = total_jinxes // 2

    # Sort editions alphabetically and character IDs within each edition
    editions = {k: sorted(v) for k, v in sorted(editions.items())}
    edition_reminders = dict(sorted(edition_reminders.items()))

    # Compute content hash for integrity checking
    char_json = json.dumps(all_chars_for_hash, sort_keys=True, ensure_ascii=False)
    content_hash = hashlib.sha256(char_json.encode()).hexdigest()

    return {
        "editions": editions,
        "edition_counts": {k: len(v) for k, v in editions.items()},
        "edition_reminders": edition_reminders,
        "total_characters": sum(len(chars) for chars in editions.values()),
        "total_reminders": total_reminders,
        "total_jinxes": total_jinxes,
        "total_flavor": total_flavor,
        "content_hash": content_hash,
    }


def build_manifest(stats: dict[str, Any]) -> dict[str, Any]:
    """Build a complete manifest dict from computed stats.

    Args:
        stats: Stats dict from compute_manifest_stats()

    Returns:
        Complete manifest dict ready for JSON serialization
    """
    return {
        "schemaVersion": SCHEMA_VERSION,
        "version": datetime.now(UTC).strftime("%Y.%m.%d"),
        "generated": datetime.now(UTC).isoformat(),
        "lastModified": datetime.now(UTC).isoformat(),
        "contentHash": stats["content_hash"],
        "source": SCRIPT_TOOL_URL,
        "total_characters": stats["total_characters"],
        "total_reminders": stats["total_reminders"],
        "total_jinxes": stats["total_jinxes"],
        "total_flavor": stats["total_flavor"],
        "editions": stats["editions"],
        "edition_counts": stats["edition_counts"],
        "edition_reminders": stats["edition_reminders"],
    }


def save_manifest(manifest: dict[str, Any], output_path: Path) -> None:
    """Save manifest to JSON file.

    Args:
        manifest: Manifest dict
        output_path: Path to save manifest file
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
