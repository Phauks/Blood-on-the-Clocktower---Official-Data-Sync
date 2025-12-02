"""
Blood on the Clocktower - Schema Validator Integration

Provides validation functions that can be integrated into the scraper pipeline.
"""

import sys
from pathlib import Path
from typing import Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from validators.schema_validator import validate_character, CHARACTER_SCHEMA
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
    print(f"\n=== Validation Summary ===")
    print(f"Valid characters: {valid}")
    print(f"Characters with errors: {errors}")
    
    if error_messages:
        print(f"\nErrors ({len(error_messages)} total):")
        # Group errors by type
        for msg in error_messages[:10]:  # Show first 10
            print(f"  - {msg}")
        if len(error_messages) > 10:
            print(f"  ... and {len(error_messages) - 10} more errors")
