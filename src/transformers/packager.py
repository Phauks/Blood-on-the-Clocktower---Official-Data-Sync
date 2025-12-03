"""
Packager for Blood on the Clocktower character data.

Creates distribution-ready package with characters.json and manifest.json
for use by the Token Generator application.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

# Handle both direct script execution and module import
try:
    from ..scrapers.config import DATA_DIR, CHARACTERS_DIR, DIST_DIR, SCRIPT_TOOL_URL, SCHEMA_VERSION
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent / "scrapers"))
    from config import DATA_DIR, CHARACTERS_DIR, DIST_DIR, SCRIPT_TOOL_URL, SCHEMA_VERSION


def load_all_characters(characters_dir: Path | None = None) -> list[dict]:
    """Load all character data from all_characters.json.

    Args:
        characters_dir: Directory containing character JSON files

    Returns:
        List of character dicts
    """
    char_dir = characters_dir or CHARACTERS_DIR
    all_file = char_dir / "all_characters.json"

    if not all_file.exists():
        raise FileNotFoundError(f"Character data not found: {all_file}")

    with open(all_file, "r", encoding="utf-8") as f:
        return json.load(f)


def create_dist_manifest(characters: list[dict], output_dir: Path) -> dict:
    """Create manifest.json for the distribution package.

    Args:
        characters: List of character dicts
        output_dir: Output directory for manifest

    Returns:
        The manifest dict
    """
    # Build editions index and count stats
    editions: dict[str, list[str]] = {}
    edition_reminders: dict[str, int] = {}
    total_reminders = 0
    total_jinxes = 0
    total_flavor = 0

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

    # Jinxes are stored on both characters, so divide by 2
    total_jinxes = total_jinxes // 2

    # Sort editions alphabetically and character IDs within each edition
    editions = {k: sorted(v) for k, v in sorted(editions.items())}
    edition_reminders = {k: v for k, v in sorted(edition_reminders.items())}

    # Compute content hash for integrity checking
    char_json = json.dumps(characters, sort_keys=True, ensure_ascii=False)
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

    manifest_file = output_dir / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return manifest


def package_data(
    output_dir: Path | None = None, characters_dir: Path | None = None, verbose: int = 0
) -> Path:
    """Create distribution package with characters.json and manifest.json.

    The package is designed to be zipped with icons/ for GitHub releases.

    Args:
        output_dir: Output directory (default: dist/)
        characters_dir: Source character data directory
        verbose: Verbosity level

    Returns:
        Path to output directory
    """
    dist_dir = output_dir or DIST_DIR
    dist_dir.mkdir(parents=True, exist_ok=True)

    if verbose >= 1:
        print(f"Creating distribution package in {dist_dir}...")

    # Load character data
    characters = load_all_characters(characters_dir)
    if verbose >= 1:
        print(f"  Loaded {len(characters)} characters")

    # Save characters.json
    chars_file = dist_dir / "characters.json"
    with open(chars_file, "w", encoding="utf-8") as f:
        json.dump(characters, f, indent=2, ensure_ascii=False)
    if verbose >= 1:
        print(f"  Created {chars_file.name}")

    # Create manifest
    manifest = create_dist_manifest(characters, dist_dir)
    if verbose >= 1:
        print(f"  Created manifest.json (v{manifest['version']}, hash: {manifest['contentHash']})")

    # Count icons (already in dist/icons from image_downloader)
    icons_dir = dist_dir / "icons"
    icon_count = sum(1 for _ in icons_dir.rglob("*.webp")) if icons_dir.exists() else 0

    print(f"Package created: {dist_dir}")
    print(f"  - characters.json ({len(characters)} characters)")
    print(f"  - manifest.json (v{manifest['version']})")
    print(f"  - icons/ ({icon_count} images)")

    return dist_dir


def verify_package(dist_dir: Path | None = None, verbose: int = 0) -> bool:
    """Verify package integrity by checking contentHash.

    Args:
        dist_dir: Distribution directory to verify
        verbose: Verbosity level

    Returns:
        True if package is valid
    """
    pkg_dir = dist_dir or DIST_DIR

    manifest_file = pkg_dir / "manifest.json"
    chars_file = pkg_dir / "characters.json"

    if not manifest_file.exists():
        print(f"Error: manifest.json not found in {pkg_dir}")
        return False

    if not chars_file.exists():
        print(f"Error: characters.json not found in {pkg_dir}")
        return False

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    with open(chars_file, "r", encoding="utf-8") as f:
        characters = json.load(f)

    # Compute hash
    char_json = json.dumps(characters, sort_keys=True, ensure_ascii=False)
    computed_hash = hashlib.sha256(char_json.encode()).hexdigest()[:16]

    if computed_hash != manifest["contentHash"]:
        print(f"Hash mismatch! Expected: {manifest['contentHash']}, Got: {computed_hash}")
        return False

    if verbose >= 1:
        print(f"Package verified: {manifest['total_characters']} characters, hash OK")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Package character data for distribution")
    parser.add_argument("--output", "-o", type=Path, help="Output directory")
    parser.add_argument("--verify", action="store_true", help="Verify existing package")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbose output")

    args = parser.parse_args()

    if args.verify:
        success = verify_package(args.output, verbose=args.verbose)
        exit(0 if success else 1)
    else:
        package_data(output_dir=args.output, verbose=args.verbose)
