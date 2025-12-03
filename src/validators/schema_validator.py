"""
Blood on the Clocktower - Schema Validator

Validates character data against the official schema from:
https://github.com/ThePandemoniumInstitute/botc-release/blob/main/script-schema.json

The official schema is designed for scripts (arrays of characters),
but we extract the character object schema for validation.
"""

import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator, ValidationError

# Add utils to path for logger
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from logger import get_logger

logger = get_logger(__name__)

# Output paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHARACTERS_DIR = DATA_DIR / "characters"

# Official schema URL
SCHEMA_URL = (
    "https://raw.githubusercontent.com/ThePandemoniumInstitute/botc-release/main/script-schema.json"
)

# Extracted character schema (from official script-schema.json)
# This is the "Script Character" object schema from the official spec
CHARACTER_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "title": "Script Character",
    "required": ["id", "name", "team", "ability"],
    "additionalProperties": False,
    "properties": {
        "id": {
            "type": "string",
            "title": "Character ID, alphanumeric lowercase",
            "maxLength": 50,
        },
        "name": {
            "type": "string",
            "title": "Character name",
            "maxLength": 30,
        },
        "image": {
            "oneOf": [
                {
                    "type": "string",
                    "format": "uri",
                    "title": "Character icon",
                },
                {
                    "type": "array",
                    "title": "Set of character icon URLs",
                    "minItems": 1,
                    "maxItems": 3,
                    "items": {"type": "string", "format": "uri"},
                },
            ]
        },
        "team": {
            "type": "string",
            "title": "Character team",
            "enum": ["townsfolk", "outsider", "minion", "demon", "traveller", "fabled", "loric"],
        },
        "edition": {
            "type": "string",
            "title": "The edition ID",
            "maxLength": 50,
        },
        "ability": {
            "type": "string",
            "title": "Character ability",
            "maxLength": 250,
        },
        "flavor": {
            "type": "string",
            "title": "Character flavor text",
            "maxLength": 500,
        },
        "firstNight": {
            "type": "number",
            "title": "First night wake-up priority. 0 means doesn't wake.",
        },
        "firstNightReminder": {
            "type": "string",
            "title": "First night Storyteller reminder",
            "maxLength": 500,
        },
        "otherNight": {
            "type": "number",
            "title": "Other nights wake-up priority. 0 means doesn't wake.",
        },
        "otherNightReminder": {
            "type": "string",
            "title": "Other nights Storyteller reminder",
            "maxLength": 500,
        },
        "reminders": {
            "type": "array",
            "maxItems": 20,
            "default": [],
            "title": "Character reminder tokens",
            "items": {"type": "string", "maxLength": 30},
        },
        "remindersGlobal": {
            "type": "array",
            "maxItems": 20,
            "default": [],
            "title": "Global character reminder tokens",
            "items": {"type": "string", "maxLength": 25},
        },
        "setup": {
            "type": "boolean",
            "title": "Whether character affects game setup",
            "default": False,
        },
        "jinxes": {
            "type": "array",
            "title": "Jinxes with other characters",
            "items": {
                "type": "object",
                "title": "An individual Jinx pair",
                "required": ["id", "reason"],
                "properties": {
                    "id": {
                        "type": "string",
                        "title": "The ID of the jinxed character",
                        "maxLength": 50,
                    },
                    "reason": {
                        "type": "string",
                        "title": "The Jinx explanation",
                        "maxLength": 500,
                    },
                },
            },
        },
        "special": {
            "type": "array",
            "title": "Special app integration features",
            "items": {
                "type": "object",
                "title": "A special app integration feature",
                "required": ["name", "type"],
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["selection", "ability", "signal", "vote", "reveal", "player"],
                    },
                    "name": {
                        "type": "string",
                        "enum": [
                            "grimoire",
                            "pointing",
                            "ghost-votes",
                            "distribute-roles",
                            "bag-disabled",
                            "bag-duplicate",
                            "multiplier",
                            "hidden",
                            "replace-character",
                            "player",
                            "card",
                            "open-eyes",
                        ],
                    },
                    "value": {
                        "oneOf": [
                            {"type": "string", "maxLength": 50},
                            {"type": "number"},
                        ]
                    },
                    "time": {
                        "type": "string",
                        "enum": [
                            "pregame",
                            "day",
                            "night",
                            "firstNight",
                            "firstDay",
                            "otherNight",
                            "otherDay",
                        ],
                    },
                    "global": {
                        "type": "string",
                        "enum": ["townsfolk", "outsider", "minion", "demon", "traveller", "dead"],
                    },
                },
            },
        },
    },
}


def create_lenient_schema() -> dict:
    """Create a more lenient schema for validation.

    The official schema uses additionalProperties: false, but we may have
    extra fields. This version allows additional properties.
    """
    schema = CHARACTER_SCHEMA.copy()
    schema["additionalProperties"] = True
    return schema


def validate_character(character: dict, strict: bool = False) -> list[str]:
    """Validate a single character against the schema.

    Args:
        character: Character data dict
        strict: If True, use strict schema (no additional properties)

    Returns:
        List of validation error messages (empty if valid)
    """
    schema = CHARACTER_SCHEMA if strict else create_lenient_schema()
    validator = Draft202012Validator(schema)

    errors = []
    for error in validator.iter_errors(character):
        path = " -> ".join(str(p) for p in error.path) if error.path else "root"
        errors.append(f"{path}: {error.message}")

    return errors


def validate_all_characters(characters: list[dict], strict: bool = False) -> dict[str, list[str]]:
    """Validate all characters and return errors by character ID.

    Args:
        characters: List of character data dicts
        strict: If True, use strict schema validation

    Returns:
        Dict mapping character ID to list of errors (only includes characters with errors)
    """
    all_errors = {}

    for character in characters:
        char_id = character.get("id", "unknown")
        errors = validate_character(character, strict=strict)
        if errors:
            all_errors[char_id] = errors

    return all_errors


def check_data_integrity(characters: list[dict]) -> list[str]:
    """Check data integrity beyond schema validation.

    Checks:
    - All character IDs are unique
    - All jinx references point to valid characters
    - Night order values are reasonable
    - Required fields are not empty strings
    """
    issues = []

    # Build ID set
    char_ids = set()
    for char in characters:
        char_id = char.get("id", "")
        if char_id in char_ids:
            issues.append(f"Duplicate character ID: {char_id}")
        char_ids.add(char_id)

    # Check jinx references
    for char in characters:
        char_id = char.get("id", "unknown")
        for jinx in char.get("jinxes", []):
            jinx_id = jinx.get("id", "")
            if jinx_id and jinx_id not in char_ids:
                issues.append(f"{char_id}: Jinx references unknown character '{jinx_id}'")

    # Check night order values
    for char in characters:
        char_id = char.get("id", "unknown")
        first_night = char.get("firstNight", 0)
        other_night = char.get("otherNight", 0)

        if first_night < 0 or first_night > 200:
            issues.append(f"{char_id}: Invalid firstNight value {first_night}")
        if other_night < 0 or other_night > 200:
            issues.append(f"{char_id}: Invalid otherNight value {other_night}")

    # Check for empty required fields
    for char in characters:
        char_id = char.get("id", "unknown")
        if not char.get("name"):
            issues.append(f"{char_id}: Empty name")
        if not char.get("ability"):
            issues.append(f"{char_id}: Empty ability")
        if not char.get("team"):
            issues.append(f"{char_id}: Empty team")

    return issues


def load_all_characters() -> list[dict]:
    """Load all characters from the combined JSON file."""
    all_file = CHARACTERS_DIR / "all_characters.json"

    if not all_file.exists():
        raise FileNotFoundError(
            f"Character data not found at {all_file}. Run character_scraper.py first."
        )

    with open(all_file, "r", encoding="utf-8") as f:
        return json.load(f)


def print_validation_report(
    schema_errors: dict[str, list[str]],
    integrity_issues: list[str],
    total_characters: int,
) -> None:
    """Print a formatted validation report."""
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION REPORT")
    logger.info("=" * 60)

    logger.info(f"\nTotal characters: {total_characters}")

    # Schema validation results
    if schema_errors:
        logger.error(f"\n❌ Schema errors: {len(schema_errors)} characters have issues")
        for char_id, errors in sorted(schema_errors.items()):
            logger.error(f"\n  {char_id}:")
            for error in errors:
                logger.error(f"    - {error}")
    else:
        logger.info("\n✓ Schema validation: All characters pass")

    # Data integrity results
    if integrity_issues:
        logger.warning(f"\n⚠️  Data integrity issues: {len(integrity_issues)}")
        for issue in integrity_issues:
            logger.warning(f"    - {issue}")
    else:
        logger.info("\n✓ Data integrity: No issues found")

    # Summary
    logger.info("\n" + "-" * 60)
    if not schema_errors and not integrity_issues:
        logger.info("✓ All validations passed!")
    else:
        total_issues = len(schema_errors) + len(integrity_issues)
        logger.warning(f"⚠️  Total issues found: {total_issues}")
    logger.info("=" * 60)


def main():
    """Main entry point for validation."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate BOTC character data")
    parser.add_argument("--strict", action="store_true", help="Use strict schema validation")
    parser.add_argument(
        "--file", type=str, help="Validate a specific JSON file instead of all_characters.json"
    )
    args = parser.parse_args()

    # Load characters
    logger.info("Loading character data...")

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Handle both single character and array
            characters = data if isinstance(data, list) else [data]
    else:
        characters = load_all_characters()

    logger.info(f"Loaded {len(characters)} characters")

    # Run validations
    logger.info("\nValidating against schema...")
    schema_errors = validate_all_characters(characters, strict=args.strict)

    logger.info("Checking data integrity...")
    integrity_issues = check_data_integrity(characters)

    # Print report
    print_validation_report(schema_errors, integrity_issues, len(characters))

    # Exit code
    if schema_errors or integrity_issues:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
