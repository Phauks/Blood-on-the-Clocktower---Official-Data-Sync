"""
Image downloader for Blood on the Clocktower character icons.

Downloads character icon images from the official script tool and saves them locally.
Supports incremental downloads (only fetches new/missing images).
"""

import time
from pathlib import Path

try:
    from tqdm import tqdm

    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

from src.scrapers.config import ICONS_DIR, IMAGE_RATE_LIMIT
from src.utils.http_client import fetch_with_retry
from src.utils.logger import get_logger

logger = get_logger(__name__)


def download_image(url: str, output_path: Path, verbose: int = 0) -> bool:
    """Download a single image from URL with retry logic.

    Args:
        url: Full URL to the image
        output_path: Local path to save the image
        verbose: Verbosity level

    Returns:
        True if download successful, False otherwise
    """
    response = fetch_with_retry(
        url,
        on_retry=lambda attempt, e: logger.debug(f"    Retry {attempt} for {output_path.name}: {e}")
        if verbose >= 1
        else None,
    )

    if not response:
        if verbose >= 1:
            logger.warning(f"    Failed to download {url} after retries")
        return False

    try:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write image data
        with open(output_path, "wb") as f:
            f.write(response.content)

        if verbose >= 2:
            logger.debug(f"    Downloaded: {output_path.name}")

        return True

    except OSError as e:
        if verbose >= 1:
            logger.error(f"    Failed to save {output_path}: {e}")
        return False


def get_local_icon_path(char_id: str, edition: str, image_url: str) -> Path:
    """Get the local path where an icon should be saved.

    Args:
        char_id: Character ID
        edition: Edition folder name
        image_url: Original image URL (to get file extension)

    Returns:
        Path object for local icon file
    """
    # Extract extension from URL (usually .webp)
    ext = Path(image_url).suffix or ".webp"

    # Organize by edition: data/icons/{edition}/{char_id}.webp
    return ICONS_DIR / edition / f"{char_id}{ext}"


def download_character_images(
    characters: dict,
    icons_dir: Path | None = None,
    incremental: bool = True,
    verbose: int = 0,
    show_progress: bool = True,
) -> dict:
    """Download icon images for all characters.

    Args:
        characters: Dict of character data (must have 'id', 'edition', '_imageUrl' or 'image' keys)
        icons_dir: Output directory for icons (default: data/icons)
        incremental: If True, skip existing images
        verbose: Verbosity level (0=quiet, 1=basic, 2=debug)
        show_progress: Show progress bar

    Returns:
        Dict with download stats: {downloaded: int, skipped: int, failed: int}
    """
    if icons_dir is None:
        icons_dir = ICONS_DIR

    icons_dir.mkdir(parents=True, exist_ok=True)

    stats = {"downloaded": 0, "skipped": 0, "failed": 0}

    # Build list of images to download
    to_download = []
    for char_id, char_data in characters.items():
        # Use _imageUrl (internal field) if available, fallback to image field
        image_url = char_data.get("_imageUrl") or char_data.get("image", "")
        edition = char_data.get("edition", "unknown")

        # Skip if no URL or if image field is already a local path
        if not image_url or not image_url.startswith("http"):
            continue

        local_path = get_local_icon_path(char_id, edition, image_url)

        # Check if already exists (incremental mode)
        if incremental and local_path.exists():
            stats["skipped"] += 1
            if verbose >= 2:
                logger.debug(f"  Skipped (exists): {char_id}")
            continue

        to_download.append((char_id, image_url, local_path))

    if not to_download:
        if verbose >= 1:
            logger.info(f"  All {stats['skipped']} images already downloaded")
        return stats

    if verbose >= 1:
        logger.info(
            f"  Downloading {len(to_download)} images ({stats['skipped']} already exist)..."
        )

    # Download with optional progress bar
    if show_progress and HAS_TQDM and not verbose:
        iterator = tqdm(to_download, desc="Downloading icons", unit="img")
    else:
        iterator = to_download

    for _char_id, image_url, local_path in iterator:
        success = download_image(image_url, local_path, verbose=verbose)

        if success:
            stats["downloaded"] += 1
        else:
            stats["failed"] += 1

        # Rate limiting (faster for images than wiki)
        time.sleep(IMAGE_RATE_LIMIT)

    return stats


if __name__ == "__main__":
    # Test: download a single character image
    import argparse

    parser = argparse.ArgumentParser(description="Download character icons")
    parser.add_argument("--char", help="Character ID to download")
    parser.add_argument("--url", help="Direct image URL")
    parser.add_argument("--edition", default="tb", help="Edition for output path")
    parser.add_argument("-v", "--verbose", action="count", default=0)

    args = parser.parse_args()

    if args.url and args.char:
        local_path = get_local_icon_path(args.char, args.edition, args.url)
        logger.info(f"Downloading {args.char} to {local_path}...")
        success = download_image(args.url, local_path, verbose=args.verbose)
        logger.info("Success!" if success else "Failed!")
    else:
        logger.info("Usage: python image_downloader.py --char imp --url <url> --edition tb")
