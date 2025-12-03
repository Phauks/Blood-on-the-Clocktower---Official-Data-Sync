"""
Extraction functions for Blood on the Clocktower scraper.

Functions for extracting character data, night order, and jinxes from the page.
"""

from typing import Any

from playwright.sync_api import Page

# Handle both direct script execution and module import
try:
    from .config import CLICK_DELAY
    from .parsers import (
        construct_full_icon_url,
        construct_local_image_path,
        detect_setup_flag,
        parse_character_id_from_icon,
        parse_edition_from_icon,
    )
except ImportError:
    from config import CLICK_DELAY
    from parsers import (
        construct_full_icon_url,
        construct_local_image_path,
        detect_setup_flag,
        parse_character_id_from_icon,
        parse_edition_from_icon,
    )

# Import logging
try:
    from ..utils.logger import get_logger
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
    from logger import get_logger

logger = get_logger(__name__)


def extract_characters(page: Page) -> dict[str, dict[str, Any]]:
    """Extract all characters from #all-characters sidebar.

    Args:
        page: Playwright page instance

    Returns:
        Dictionary mapping character IDs to character data dictionaries
    """
    characters = {}

    char_elements = page.query_selector_all("#all-characters .item[data-id]")
    logger.info(f"Found {len(char_elements)} characters in sidebar")

    for elem in char_elements:
        char_id = elem.get_attribute("data-id")
        if not char_id:
            continue

        # Get character name
        name_elem = elem.query_selector(".character-name")
        name = name_elem.text_content().strip() if name_elem else char_id.title()

        # Get team type
        team = elem.get_attribute("data-type") or "unknown"

        # Get ability text
        ability_elem = elem.query_selector(".ability-text")
        ability = ability_elem.text_content().strip() if ability_elem else ""

        # Get icon source and parse edition
        img_elem = elem.query_selector("img")
        icon_src = img_elem.get_attribute("src") if img_elem else ""
        edition = parse_edition_from_icon(icon_src)
        image_url = construct_full_icon_url(icon_src)
        local_image_path = construct_local_image_path(edition, char_id, icon_src)

        characters[char_id] = {
            "id": char_id,
            "name": name,
            "team": team,
            "ability": ability,
            "edition": edition,
            "image": local_image_path,
            "_imageUrl": image_url,  # Internal: used for downloading, stripped before output
            "firstNight": 0,
            "firstNightReminder": "",
            "otherNight": 0,
            "otherNightReminder": "",
            "reminders": [],
            "remindersGlobal": [],
            "setup": detect_setup_flag(char_id, ability),
            "jinxes": [],
        }

    return characters


def extract_night_order(
    page: Page, characters: dict[str, dict[str, Any]], selector: str, night_type: str
) -> None:
    """Extract night order from first-night or other-night sheet.

    Args:
        page: Playwright page instance
        characters: Character dictionary to update in-place
        selector: CSS selector for night sheet (.first-night or .other-night)
        night_type: Field name - either "firstNight" or "otherNight"

    Note:
        Modifies the characters dictionary in-place
    """
    reminder_key = f"{night_type}Reminder"

    items = page.query_selector_all(f"{selector} .item")
    logger.info(f"Found {len(items)} items in {night_type} order")

    order = 0
    for item in items:
        # Get character icon to extract ID
        img_elem = item.query_selector("img")
        if not img_elem:
            continue

        icon_src = img_elem.get_attribute("src") or ""
        char_id = parse_character_id_from_icon(icon_src)

        # Skip non-character entries (Dusk, Dawn, MINION, DEMON info, etc.)
        if not char_id or char_id not in characters:
            continue

        order += 1

        # Get reminder text
        reminder_elem = item.query_selector(".night-sheet-reminder")
        if reminder_elem:
            reminder_text = reminder_elem.text_content().strip()

            characters[char_id][night_type] = order
            characters[char_id][reminder_key] = reminder_text
        else:
            characters[char_id][night_type] = order


def extract_jinxes(page: Page, characters: dict[str, dict[str, Any]]) -> int:
    """Extract all jinxes from the Djinn section.

    Jinxes are stored bidirectionally on both characters involved.

    Args:
        page: Playwright page instance
        characters: Character dictionary to update in-place

    Returns:
        Number of jinx pairs extracted

    Note:
        Modifies the characters dictionary by adding jinx entries
    """
    jinx_items = page.query_selector_all(".jinxes-container .jinxes .item")
    logger.info(f"Found {len(jinx_items)} jinx pairs")

    jinx_count = 0

    for jinx_item in jinx_items:
        # Get the two character icons
        icons = jinx_item.query_selector_all(".icons img.icon")
        if len(icons) != 2:
            continue

        char1_src = icons[0].get_attribute("src") or ""
        char2_src = icons[1].get_attribute("src") or ""

        char1_id = parse_character_id_from_icon(char1_src)
        char2_id = parse_character_id_from_icon(char2_src)

        if not char1_id or not char2_id:
            continue

        # Get jinx rule text
        jinx_text_elem = jinx_item.query_selector(".jinx-text")
        if not jinx_text_elem:
            continue

        jinx_text = jinx_text_elem.text_content().strip()

        # Add jinx to first character (pointing to second)
        if char1_id in characters:
            characters[char1_id]["jinxes"].append(
                {
                    "id": char2_id,
                    "reason": jinx_text,
                }
            )

        # Add jinx to second character (pointing to first)
        if char2_id in characters:
            characters[char2_id]["jinxes"].append(
                {
                    "id": char1_id,
                    "reason": jinx_text,
                }
            )

        jinx_count += 1

    return jinx_count


def add_all_characters_to_script(page: Page) -> None:
    """Click all characters to add them to the script.

    This is necessary to expose night order and jinx data in the UI.
    Uses batch JavaScript execution for speed (clicks all at once).

    Args:
        page: Playwright page instance

    Note:
        Executes JavaScript to click all character elements simultaneously
    """
    # Count characters first
    count = page.evaluate("""
        () => document.querySelectorAll('#all-characters .item[data-id]').length
    """)
    logger.info(f"Adding {count} characters to script...")

    # Click all characters in a single JavaScript call (MUCH faster)
    result = page.evaluate("""
        () => {
            const items = document.querySelectorAll('#all-characters .item[data-id]');
            let added = 0;
            let failed = 0;
            items.forEach(item => {
                try {
                    item.click();
                    added++;
                } catch (e) {
                    failed++;
                }
            });
            return { added, failed };
        }
    """)

    # Wait for the script to update
    page.wait_for_timeout(CLICK_DELAY)
    logger.info(f"Added {result['added']} characters to script ({result['failed']} failed)")


def clean_character_data(characters: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Clean up character data before output.

    Removes empty jinxes arrays for cleaner JSON output.

    Args:
        characters: Character dictionary to clean

    Returns:
        Cleaned character dictionary (same object, modified in-place)

    Note:
        Internal fields (underscore-prefixed like _imageUrl) are NOT stripped here.
        They are stripped in writers.py when saving to JSON files.
    """
    for _char_id, char in list(characters.items()):
        # Remove empty jinxes arrays for cleaner output
        if "jinxes" in char and not char["jinxes"]:
            del char["jinxes"]

    return characters


def filter_characters_by_edition(
    characters: dict[str, dict[str, Any]], editions: list[str]
) -> dict[str, dict[str, Any]]:
    """Filter characters to only include specified editions.

    Args:
        characters: Full character dictionary
        editions: List of edition IDs to include (e.g., ["tb", "bmr"])

    Returns:
        Filtered character dict
    """
    return {char_id: char for char_id, char in characters.items() if char["edition"] in editions}
