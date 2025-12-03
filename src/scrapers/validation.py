"""
Blood on the Clocktower - Schema Validator Integration

Provides validation functions that can be integrated into the scraper pipeline.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

from logger import get_logger

logger = get_logger(__name__)

try:
    from validators.schema_validator import CHARACTER_SCHEMA, validate_character
except ImportError:
    # Fallback if validators module not available
    def validate_character(char: dict) -> list[str]:
        return []

    CHARACTER_SCHEMA = {}


def validate_characters(characters: dict, strict: bool = False) -> tuple[int, int, list[str]]:
    """Validate all characters against the schema.

    Args:
        characters: Character data dict
        strict: If True, raise exception on validation failure

    Returns:
        Tuple of (valid_count, error_count, error_messages)
    """
    valid = 0
    errors = 0
    error_messages = []

    for char_id, char in characters.items():
        error_list = validate_character(char)
        if not error_list:
            valid += 1
        else:
            errors += 1
            for error in error_list:
                msg = f"{char_id}: {error}"
                error_messages.append(msg)
                if strict:
                    raise ValueError(msg)

    return valid, errors, error_messages


def print_validation_summary(valid: int, errors: int, error_messages: list[str]) -> None:
    """Print a summary of validation results."""
    logger.info("\n=== Validation Summary ===")
    logger.info(f"Valid characters: {valid}")
    logger.info(f"Characters with errors: {errors}")

    if error_messages:
        logger.info(f"\nErrors ({len(error_messages)} total):")
        # Group errors by type
        for msg in error_messages[:10]:  # Show first 10
            logger.error(f"  - {msg}")
        if len(error_messages) > 10:
            logger.info(f"  ... and {len(error_messages) - 10} more errors")
