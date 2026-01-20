"""
Blood on the Clocktower - Official Character Data Scraper

Extracts all character data from the official script tool:
https://script.bloodontheclocktower.com/

Usage:
    python character_scraper.py                    # Scrape all characters
    python character_scraper.py --all             # Full pipeline: validate + images + reminders
    python character_scraper.py --edition tb bmr  # Only specific editions
    python character_scraper.py --no-headless     # Show browser window
    python character_scraper.py --validate        # Run schema validation after scrape
    python character_scraper.py --images          # Download character icon images
    python character_scraper.py --reminders       # Fetch reminder tokens from wiki
    python character_scraper.py --output-dir ./out # Custom output directory

Data Sources (single page load):
1. Character List (#all-characters) → id, name, team, ability, edition, image
2. First Night Sheet (.first-night) → firstNight order, firstNightReminder
3. Other Night Sheet (.other-night) → otherNight order, otherNightReminder
4. Jinxes (.jinxes-container) → jinx pairs (131 total)
5. Setup Flag → Pattern matching on ability text

Note: Reminder tokens are empty [] by default. Use --reminders to fetch them
from wiki "How to Run" sections (adds ~1 sec per character).
"""

import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from src.utils.logger import get_logger

logger = get_logger(__name__)

from src.scrapers.config import (  # noqa: E402
    CHARACTERS_DIR,
    DATA_DIR,
    DEFAULT_TIMEOUT,
    ICONS_DIR,
    PAGE_RENDER_DELAY,
    SCRIPT_TOOL_URL,
    VALID_EDITIONS,
)
from src.scrapers.extractors import (  # noqa: E402
    add_all_characters_to_script,
    clean_character_data,
    extract_characters,
    extract_jinxes,
    extract_night_order,
    filter_characters_by_edition,
)
from src.scrapers.validation import print_validation_summary, validate_characters  # noqa: E402
from src.scrapers.writers import create_manifest, save_characters_by_edition  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape Blood on the Clocktower character data from the official script tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          Scrape all characters
  %(prog)s --edition tb bmr         Only Trouble Brewing and Bad Moon Rising
  %(prog)s --no-headless            Show browser window (useful for debugging)
  %(prog)s --validate               Validate data against schema after scraping
  %(prog)s --output-dir ./output    Save to custom directory
        """,
    )

    parser.add_argument(
        "--edition",
        "-e",
        nargs="+",
        choices=list(VALID_EDITIONS),
        help="Only scrape specific editions (default: all)",
        metavar="EDITION",
    )

    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Show browser window instead of running headless",
    )

    parser.add_argument(
        "--validate",
        "-v",
        action="store_true",
        help="Run schema validation after scraping",
    )

    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        help="Custom output directory for character data",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Page load timeout in milliseconds (default: {DEFAULT_TIMEOUT})",
    )

    parser.add_argument(
        "--reminders",
        "-r",
        action="store_true",
        help="Fetch reminder tokens from wiki (adds ~1 sec per character)",
    )

    parser.add_argument(
        "--flavor",
        "-f",
        action="store_true",
        help="Fetch flavor text from wiki (adds ~1 sec per character)",
    )

    parser.add_argument(
        "--images",
        "-i",
        action="store_true",
        help="Download character icon images (incremental, skips existing)",
    )

    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Enable all optional features: --validate --images --reminders --flavor --package",
    )

    parser.add_argument(
        "--package",
        "-p",
        action="store_true",
        help="Create distribution package in dist/ for Token Generator",
    )

    args = parser.parse_args()

    # --all flag enables all optional features
    if args.all:
        args.validate = True
        args.images = True
        args.reminders = True
        args.flavor = True
        args.package = True

    return args


def scrape_characters(headless: bool = True, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Main scraper function. Returns character data dict."""
    logger.info(f"Starting scrape of {SCRIPT_TOOL_URL}")

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()

        # Navigate to script tool
        logger.info("Loading page...")
        page.goto(SCRIPT_TOOL_URL, timeout=timeout)

        # Wait for character list to load (Single Page Application renders content dynamically)
        logger.info("Waiting for Single Page Application to render...")
        page.wait_for_selector("#all-characters .item[data-id]", state="attached", timeout=timeout)
        # Give the page a moment to fully render
        page.wait_for_timeout(PAGE_RENDER_DELAY)
        logger.info("Page loaded successfully")

        # Phase 1: Extract character list
        logger.info("\n--- Phase 1: Extracting characters ---")
        characters = extract_characters(page)

        # Phase 2: Add all characters to script (enables night order and jinxes)
        logger.info("\n--- Phase 2: Adding characters to script ---")
        add_all_characters_to_script(page)

        # Phase 3: Extract first night order from active script
        logger.info("\n--- Phase 3: Extracting first night order ---")
        extract_night_order(page, characters, ".first-night", "firstNight")

        # Phase 4: Extract other night order from active script
        logger.info("\n--- Phase 4: Extracting other night order ---")
        extract_night_order(page, characters, ".other-night", "otherNight")

        # Phase 5: Extract jinxes (should now be visible with Djinn in script)
        logger.info("\n--- Phase 5: Extracting jinxes ---")
        jinx_count = extract_jinxes(page, characters)

        browser.close()

    # Clean up data
    characters = clean_character_data(characters)

    # Print summary
    logger.info("\n=== Extraction Summary ===")
    logger.info(f"Total characters: {len(characters)}")
    logger.info(f"Total jinx pairs: {jinx_count}")

    chars_with_first_night = sum(1 for c in characters.values() if c["firstNight"] > 0)
    chars_with_other_night = sum(1 for c in characters.values() if c["otherNight"] > 0)
    chars_with_setup = sum(1 for c in characters.values() if c["setup"])
    chars_with_jinxes = sum(1 for c in characters.values() if "jinxes" in c and c["jinxes"])

    logger.info(f"Characters with first night action: {chars_with_first_night}")
    logger.info(f"Characters with other night action: {chars_with_other_night}")
    logger.info(f"Characters with setup: {chars_with_setup}")
    logger.info(f"Characters with jinxes: {chars_with_jinxes}")

    # Count by edition
    edition_counts = {}
    for char in characters.values():
        edition = char["edition"]
        edition_counts[edition] = edition_counts.get(edition, 0) + 1

    logger.info("\nBy edition:")
    for edition, count in sorted(edition_counts.items()):
        logger.info(f"  {edition}: {count}")

    return characters


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Determine output directories
    if args.output_dir:
        output_dir = args.output_dir
        char_dir = output_dir / "characters"
        data_dir = output_dir
    else:
        char_dir = CHARACTERS_DIR
        data_dir = DATA_DIR

    # Ensure output directories exist
    char_dir.mkdir(parents=True, exist_ok=True)
    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    # Run scraper
    characters = scrape_characters(
        headless=not args.no_headless,
        timeout=args.timeout,
    )

    # Filter by edition if requested
    if args.edition:
        logger.info(f"\n--- Filtering to editions: {', '.join(args.edition)} ---")
        characters = filter_characters_by_edition(characters, args.edition)
        logger.info(f"Filtered to {len(characters)} characters")

    # Validate if requested
    if args.validate:
        logger.info("\n--- Phase 6: Validating data ---")
        valid, errors, error_messages = validate_characters(characters)
        print_validation_summary(valid, errors, error_messages)
        if errors > 0:
            logger.warning("\n⚠ Validation found issues (non-blocking)")

    # Download images if requested (BEFORE saving, while _imageUrl is still present)
    if args.images:
        logger.info("\n--- Downloading character icons (incremental) ---")
        try:
            from src.scrapers.image_downloader import download_character_images

            stats = download_character_images(
                characters, icons_dir=ICONS_DIR, incremental=True, verbose=0, show_progress=True
            )

            logger.info(
                f"\n✓ Images: {stats['downloaded']} downloaded, {stats['skipped']} skipped, {stats['failed']} failed"
            )
        except ImportError as e:
            logger.warning(f"\n⚠ Could not import image_downloader: {e}")

    # Load previous data BEFORE saving (for incremental reminder fetching)
    previous_data = None
    if args.reminders:
        try:
            from src.transformers.reminder_fetcher import load_previous_character_data

            previous_data = load_previous_character_data()
        except ImportError:
            pass

    # Save output (this strips internal fields like _imageUrl)
    logger.info("\n--- Saving data ---")
    save_characters_by_edition(characters, char_dir)
    create_manifest(characters, data_dir)

    # Fetch reminders from wiki if requested
    if args.reminders:
        logger.info("\n--- Phase 7: Fetching reminder tokens from wiki (incremental) ---")
        try:
            from src.transformers.reminder_fetcher import (
                fetch_reminders_for_edition,
                update_character_files_with_reminders,
            )

            # Determine which editions to fetch
            editions_to_fetch = args.edition if args.edition else list(VALID_EDITIONS)

            total_tokens = 0
            total_fetched = 0
            total_preserved = 0

            for edition in editions_to_fetch:
                result = fetch_reminders_for_edition(
                    edition,
                    dry_run=False,
                    team_filter=None,
                    verbose=0,
                    show_progress=True,
                    incremental=True,
                    previous_data=previous_data,
                )
                if result and result.get("reminders"):
                    update_character_files_with_reminders(edition, result["reminders"])
                    total_tokens += result.get("total_tokens", 0)
                    total_fetched += result.get("fetched", 0)
                    total_preserved += result.get("preserved", 0)

            logger.info("\nReminder summary:")
            logger.info(f"  Fetched: {total_fetched}, Preserved: {total_preserved}")
            logger.info(f"  Total reminder tokens: {total_tokens}")
            logger.info("\n✓ Reminder tokens fetched (only new/changed characters)!")
        except ImportError as e:
            logger.warning(f"\n⚠ Could not import reminder_fetcher: {e}")
            logger.warning("  Run 'pip install beautifulsoup4 tqdm' and try again.")

    # Fetch flavor text from wiki if requested
    if args.flavor:
        logger.info("\n--- Phase 8: Fetching flavor text from wiki (incremental) ---")
        try:
            from src.transformers.flavor_fetcher import (
                load_scraped_characters,
                save_updated_characters,
                update_flavor_for_characters,
            )

            # Load current character data
            char_data = load_scraped_characters()

            # Update flavor text
            stats = update_flavor_for_characters(char_data, force=False)

            # Save if any fetches were made
            if stats["fetched"] > 0:
                save_updated_characters(char_data)

            logger.info("\n✓ Flavor text fetched (only new/changed characters)!")
        except ImportError as e:
            logger.warning(f"\n⚠ Could not import flavor_fetcher: {e}")
            logger.warning("  Run 'pip install beautifulsoup4' and try again.")

    # Create distribution package if requested
    if args.package:
        logger.info("\n--- Phase 9: Creating distribution package ---")
        try:
            from packager import package_data

            package_data(verbose=1)
            logger.info("\n✓ Distribution package created in dist/")
        except ImportError as e:
            logger.warning(f"\n⚠ Could not import packager: {e}")

    # Regenerate manifest with updated data (reminders, flavor, etc.)
    if args.reminders or args.flavor:
        logger.info("\n--- Updating manifest with fetched data ---")
        try:
            from data_loader import load_previous_character_data as load_all_chars

            updated_characters = load_all_chars()
            if updated_characters:
                create_manifest(updated_characters, data_dir)
        except ImportError:
            pass

    logger.info("\n✓ Scraping complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
