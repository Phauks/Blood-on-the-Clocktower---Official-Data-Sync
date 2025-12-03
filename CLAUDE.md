# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

This repository automatically syncs official Blood on the Clocktower character data from the official script tool and official game wikipedia and publishes versioned releases for community tools.

**Official Data Source:** https://script.bloodontheclocktower.com/
**Official Wiki Source:** https://wiki.bloodontheclocktower.com/

## Quick Start Commands

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run FULL pipeline (scrape, validate, images, reminders)
python src/scrapers/character_scraper.py --all

# Run the scraper (all editions)
python src/scrapers/character_scraper.py

# Run with specific editions
python src/scrapers/character_scraper.py --edition tb bmr snv

# Run with validation
python src/scrapers/character_scraper.py --validate

# Download character icons
python src/scrapers/character_scraper.py --images

# Fetch reminder tokens from wiki (incremental)
python src/scrapers/character_scraper.py --reminders

# Run with visible browser (debugging)
python src/scrapers/character_scraper.py --no-headless

# Validate existing data
python src/validators/schema_validator.py

# Run reminder fetcher standalone
python src/transformers/reminder_fetcher.py -v
```

## Project Structure

```
data/
  characters/{edition}/     # Individual character JSON files
  characters/all_characters.json  # Combined file with all characters
  icons/{edition}/          # Character icons (WebP)
  manifest.json             # Master index with version info
src/
  scrapers/                 # Web scraping logic (modular architecture)
    character_scraper.py    # Main entry point with CLI
    config.py               # Centralized constants and HTTP settings
    parsers.py              # Text parsing utilities
    extractors.py           # Page extraction functions
    writers.py              # File output functions
    validation.py           # Schema validation integration
    image_downloader.py     # Download character icons from script tool
  transformers/             # Data transformation
    flavor_fetcher.py       # Wiki flavor text (incremental)
    reminder_fetcher.py     # Wiki reminder tokens (incremental)
  utils/                    # Shared utilities
    http_client.py          # HTTP requests with retry logic
    data_loader.py          # Character data loading/saving
  validators/               # Schema validation
    schema_validator.py     # Validates against official schema
research/                   # Archived analysis documents
```

## Scraper Architecture

The scraper is organized into modular components:

- **`config.py`** - Centralized constants:
  - `SCRIPT_TOOL_URL` - Official script tool URL
  - `WIKI_BASE_URL` - Official wiki URL
  - `BASE_ICON_URL` - Icon URL base path
  - `SETUP_CHARACTERS` - Set of characters with setup abilities
  - Path constants: `PROJECT_ROOT`, `DATA_DIR`, `CHARACTERS_DIR`, `ICONS_DIR`
  - HTTP settings: `REQUEST_TIMEOUT`, `HTTP_MAX_RETRIES`, `HTTP_RETRY_BACKOFF`, `USER_AGENT`

- **`parsers.py`** - Pure parsing functions:
  - `parse_edition_from_icon(src)` - Extract edition from icon URL
  - `parse_character_id_from_icon(src)` - Extract character ID from icon URL
  - `construct_full_icon_url(edition, char_id, team)` - Build full icon URL
  - `detect_setup_flag(ability, char_id)` - Detect setup modifiers in ability text

- **`extractors.py`** - Page interaction and data extraction:
  - `extract_characters(page)` - Get all characters from sidebar
  - `add_all_characters_to_script(page, characters)` - Click to add characters
  - `extract_night_order(page, night_type)` - Get night order from sheets
  - `extract_jinxes(page)` - Get all jinx pairs
  - `clean_character_data(characters)` - Remove internal fields

- **`writers.py`** - File output:
  - `save_characters_by_edition(characters, output_dir, editions)` - Save individual files
  - `create_manifest(output_dir, characters, jinxes)` - Create manifest.json

- **`validation.py`** - Schema validation:
  - `validate_all_characters(characters)` - Validate against official schema

- **`image_downloader.py`** - Icon downloading:
  - `download_character_icons(characters, output_dir, verbose)` - Download icons with retry

## Shared Utilities (src/utils/)

- **`http_client.py`** - HTTP requests with retry logic:
  - `fetch_with_retry(url, max_retries, backoff, on_retry)` - Exponential backoff retry
  - `rate_limit(seconds)` - Sleep wrapper for rate limiting

- **`data_loader.py`** - Character data loading:
  - `load_previous_character_data(edition, char_id)` - Load existing JSON
  - `save_character_file(char_data, edition, char_id)` - Save character JSON
  - `get_character_files_by_edition()` - List all character files by edition

- **`logger.py`** - Centralized logging:
  - `setup_logger(name, level)` - Configure logger with console and file handlers
  - `get_logger(name)` - Get or create logger instance
  - UTF-8 encoding support for Unicode characters (checkmarks, etc.)
  - Logs to both console (INFO+) and file (DEBUG+)

- **`wiki_client.py`** - Wiki URL construction and fetching:
  - `normalize_wiki_name(character_name)` - Convert name to wiki URL format
  - `construct_wiki_url(character_name, validate)` - Build full wiki URL with SSRF protection
  - `fetch_wiki_page(character_name)` - Fetch wiki page with retry logic
  - `rate_limit(seconds)` - Rate limiting for wiki requests

## Logging

The project uses Python's built-in `logging` module with centralized configuration in `src/utils/logger.py`.

**Getting a Logger:**
```python
from logger import get_logger

logger = get_logger(__name__)  # Auto-configures if needed
logger.info("Starting process")
logger.warning("Potential issue detected")
logger.error("Operation failed")
logger.debug("Detailed debug information")
```

**Log Levels:**
- **DEBUG**: Detailed information for debugging (file only)
- **INFO**: Confirmation that things are working (console + file)
- **WARNING**: Something unexpected but handled (console + file)
- **ERROR**: Serious problem, operation failed (console + file)

**Verbose Mode:**
Many scripts support `-v` flag for more detailed output:
```bash
python src/transformers/reminder_fetcher.py -v
python src/scrapers/character_scraper.py -v
```

**Log Output:**
- Console: INFO level and above, with color-coded levels
- File: `scraper.log` with DEBUG level and above, includes timestamps
- UTF-8 encoding ensures Unicode characters (✓, ✗) display correctly on Windows

## Configuration

All configurable constants are centralized in `src/scrapers/config.py`:

**URLs and Endpoints:**
```python
SCRIPT_TOOL_URL = "https://script.bloodontheclocktower.com"
WIKI_BASE_URL = "https://wiki.bloodontheclocktower.com"
BASE_ICON_URL = "https://script.bloodontheclocktower.com/"
```

**File Paths:**
```python
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHARACTERS_DIR = DATA_DIR / "characters"
ICONS_DIR = DATA_DIR / "icons"
```

**HTTP Settings:**
```python
REQUEST_TIMEOUT = 30          # seconds
HTTP_MAX_RETRIES = 3          # number of retry attempts
HTTP_RETRY_BACKOFF = 1.0      # base backoff in seconds (1s → 2s → 4s)
USER_AGENT = "BOTC-Data-Sync/1.0"
```

**Scraper Settings:**
```python
PAGE_LOAD_TIMEOUT = 60000     # milliseconds for Playwright
PAGE_RENDER_DELAY = 2000      # milliseconds for Vue.js to render
CLICK_DELAY = 500             # milliseconds after adding characters
RATE_LIMIT_SECONDS = 0.5      # delay between wiki requests
IMAGE_RATE_LIMIT = 0.2        # delay between icon downloads
```

**Setup Characters:**
```python
SETUP_EXCEPTIONS = {
    "drunk",          # False identity without bracket text
    "sentinel",       # Fabled with prose description
    "deusexfiasco",   # Fabled: Storyteller makes mistakes
}
```

**How to Modify Settings:**
1. Edit values in `config.py`
2. All modules import from this central location
3. Changes apply project-wide automatically
4. Restart any running processes to pick up changes

## Reminder Token Fetcher (src/transformers/reminder_fetcher.py)

Fetches reminder tokens from the official wiki (incremental updates only):

- Uses `_remindersFetched` internal flag to track which characters need fetching
- Skips characters where reminders were already fetched
- Characters with no reminder tokens have `reminders: []` (valid, not an error)
- Supports verbose mode (`-v`) and progress bar (tqdm)
- Uses HTTP retry with exponential backoff

## CLI Arguments

```
--all, -a                             Run full pipeline (validate + images + reminders)
--edition, -e EDITION [EDITION ...]   Only scrape specific editions (default: all)
--no-headless                         Show browser window for debugging
--validate                            Run schema validation after scraping
--images, -i                          Download character icons
--reminders, -r                       Fetch reminder tokens from wiki
--output-dir, -o PATH                 Custom output directory
--timeout MS                          Page load timeout (default: 60000)
-v                                    Verbose output
```

## Data Extraction Strategy

All character data is extracted from a single page load of the script tool:

1. **Character List** (`#all-characters`) → id, name, team, ability, edition, image
2. **First Night Sheet** (`.first-night`) → firstNight order, firstNightReminder
3. **Other Night Sheet** (`.other-night`) → otherNight order, otherNightReminder
4. **Jinxes** (`.jinxes-container`) → jinx pairs (131 total)
5. **Setup Flag** → Pattern matching on ability text (`[+N Outsider]`, etc.)
6. **Reminder Tokens** → Fetched from wiki via `--reminders` flag (incremental)
7. **Character Icons** → Downloaded from script tool via `--images` flag

## Data Constraints

- **Only use official sources** - Script tool for character data, wiki for reminder tokens
- **Reminder tokens** - Fetched from wiki. Characters without reminder tokens have `reminders: []`
- **`_remindersFetched` flag** - Internal flag to track which characters have had reminders fetched
- **Schema validation** - Character data must validate against the official schema. Use `--validate` flag or run `schema_validator.py`.

## Key Technical Details

- **Icon URL Pattern:** `https://script.bloodontheclocktower.com/src/assets/icons/{edition}/{id}{suffix}.webp`
  - `_g` suffix for good (townsfolk, outsider)
  - `_e` suffix for evil (minion, demon)
  - No suffix for traveller/fabled
- **HTTP Retry:** All HTTP requests use exponential backoff (1s → 2s → 4s), max 3 retries
- **Total Characters:** 174
- **Total Jinxes:** 131 pairs
- **Editions:** tb (Trouble Brewing), bmr (Bad Moon Rising), snv (Sects & Violets), carousel, loric, fabled

## Testing

The project uses pytest for testing with organized test categories.

**Running Tests:**
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_parsers.py

# Run specific test class
pytest tests/unit/test_parsers.py::TestParseEditionFromIcon

# Run specific test
pytest tests/unit/test_parsers.py::TestParseEditionFromIcon::test_parse_tb_edition

# Run tests by marker
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests only
pytest -m e2e         # End-to-end tests only
pytest -m slow        # Slow tests only

# Run with coverage report
pytest --cov=src --cov-report=html --cov-report=term
```

**Test Organization:**
- `tests/unit/` - Fast, isolated tests for individual functions
- `tests/integration/` - Tests for multi-module interactions
- `tests/e2e/` - End-to-end tests (may require network access)
- `tests/conftest.py` - Shared pytest fixtures

**Test Markers:**
- `@pytest.mark.unit` - Unit test (fast, no external dependencies)
- `@pytest.mark.integration` - Integration test (multiple modules)
- `@pytest.mark.e2e` - End-to-end test (slow, may use network)
- `@pytest.mark.slow` - Any test that takes significant time

**Available Fixtures (tests/conftest.py):**
- `sample_character` - Sample character data dictionary
- `sample_characters` - List of multiple characters
- `temp_dir` - Temporary directory for test outputs (auto-cleanup)
- `mock_response` - Mock HTTP response object
- `mock_wiki_page` - Mock wiki HTML page
- `project_root` - Project root directory path
- `data_dir` - Data directory path
- `test_output_dir` - Test output directory (auto-cleanup)

**Writing Tests:**
```python
import pytest
from parsers import parse_edition_from_icon

class TestParseEdition:
    """Tests for parse_edition_from_icon function."""

    @pytest.mark.unit
    def test_parse_tb_edition(self):
        """Should extract 'tb' edition from icon path."""
        icon_src = "src/assets/icons/tb/washerwoman_g.webp"
        assert parse_edition_from_icon(icon_src) == "tb"
```

**Test Coverage Goals:**
- Unit tests: 80%+ coverage for parsers, utilities, validators
- Integration tests: Critical workflows (HTTP retry, wiki fetching)
- E2E tests: Full scraper pipeline (optional, slow)

**Test Configuration:**
See `pytest.ini` for pytest settings including markers, test paths, and output options.

## Development Notes

- The script tool is a Vue.js SPA - must wait for JavaScript rendering
- Use JavaScript clicks (`evaluate`) when Playwright clicks timeout
- Night order extraction requires characters to be added to the script first
- Import pattern uses try/except for relative vs absolute imports (supports both direct execution and module import)

## Attribution

Blood on the Clocktower © The Pandemonium Institute. This is an unofficial fan project.
See `data/ATTRIBUTION.md` for full licensing.
