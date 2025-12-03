"""
Blood on the Clocktower scrapers package.

Modules:
- config: Configuration constants (URLs, paths, setup characters)
- parsers: Text parsing utilities (icon URLs, setup detection)
- extractors: Page extraction functions (characters, night order, jinxes)
- writers: File output functions (JSON, manifest)
- validation: Schema validation integration
- character_scraper: Main scraper entry point with CLI
"""

from .config import (
    SCRIPT_TOOL_URL,
    WIKI_BASE_URL,
    CHARACTERS_DIR,
    DATA_DIR,
    VALID_EDITIONS,
    VALID_TEAMS,
)

__all__ = [
    "SCRIPT_TOOL_URL",
    "WIKI_BASE_URL",
    "CHARACTERS_DIR",
    "DATA_DIR",
    "VALID_EDITIONS",
    "VALID_TEAMS",
]
