"""
Packager for Blood on the Clocktower character data.

Creates distribution-ready package with characters.json and manifest.json
for use by the Token Generator application.
"""

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path for direct script execution
if __name__ == "__main__" or "src" not in sys.modules:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scrapers.config import CHARACTERS_DIR, DIST_DIR
from src.utils.logger import get_logger
from src.utils.manifest_utils import build_manifest, compute_manifest_stats, save_manifest

logger = get_logger(__name__)


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

    with open(all_file, encoding="utf-8") as f:
        data: list[dict[Any, Any]] = json.load(f)
        return data


def create_dist_manifest(characters: list[dict], output_dir: Path) -> dict:
    """Create manifest.json for the distribution package.

    Args:
        characters: List of character dicts
        output_dir: Output directory for manifest

    Returns:
        The manifest dict
    """
    # Compute stats and build manifest using shared utilities
    stats = compute_manifest_stats(characters)
    manifest = build_manifest(stats)

    # Save manifest
    manifest_file = output_dir / "manifest.json"
    save_manifest(manifest, manifest_file)

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
        logger.info(f"Creating distribution package in {dist_dir}...")

    # Load character data
    characters = load_all_characters(characters_dir)
    if verbose >= 1:
        logger.info(f"  Loaded {len(characters)} characters")

    # Save characters.json
    chars_file = dist_dir / "characters.json"
    with open(chars_file, "w", encoding="utf-8") as f:
        json.dump(characters, f, indent=2, ensure_ascii=False)
    if verbose >= 1:
        logger.info(f"  Created {chars_file.name}")

    # Create manifest
    manifest = create_dist_manifest(characters, dist_dir)
    if verbose >= 1:
        logger.info(
            f"  Created manifest.json (v{manifest['version']}, hash: {manifest['contentHash']})"
        )

    # Count icons (already in dist/icons from image_downloader)
    icons_dir = dist_dir / "icons"
    icon_count = sum(1 for _ in icons_dir.rglob("*.webp")) if icons_dir.exists() else 0

    logger.info(f"Package created: {dist_dir}")
    logger.info(f"  - characters.json ({len(characters)} characters)")
    logger.info(f"  - manifest.json (v{manifest['version']})")
    logger.info(f"  - icons/ ({icon_count} images)")

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
        logger.error(f"Error: manifest.json not found in {pkg_dir}")
        return False

    if not chars_file.exists():
        logger.error(f"Error: characters.json not found in {pkg_dir}")
        return False

    with open(manifest_file, encoding="utf-8") as f:
        manifest = json.load(f)

    with open(chars_file, encoding="utf-8") as f:
        characters = json.load(f)

    # Compute hash
    char_json = json.dumps(characters, sort_keys=True, ensure_ascii=False)
    computed_hash = hashlib.sha256(char_json.encode()).hexdigest()

    if computed_hash != manifest["contentHash"]:
        logger.error(f"Hash mismatch! Expected: {manifest['contentHash']}, Got: {computed_hash}")
        return False

    if verbose >= 1:
        logger.info(f"Package verified: {manifest['total_characters']} characters, hash OK")

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
