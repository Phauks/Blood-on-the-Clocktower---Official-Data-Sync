# TODO

## High Priority

### Reminder Tokens
- [x] Implement wiki scraper for reminder tokens (`reminder_fetcher.py`)
- [x] Scrape "HOW TO RUN" sections from `https://wiki.bloodontheclocktower.com/{Character_Name}`
- [x] Extract tokens using pattern: `([A-Z][A-Z\s]+)\s+reminder`
- [x] Handle deduplication (e.g., Witch mentions "CURSED" multiple times)
- [x] Distinguish `reminders` vs `remindersGlobal` (remindersGlobal always empty)

## Medium Priority

## Low Priority

### Enhancements
- [x] Add incremental update mode (reminders, images, flavor all support incremental)
- [x] Download and cache icon images locally (`--images` flag, `image_downloader.py`)
- [x] Add flavor text from wiki (`flavor_fetcher.py`)

## Completed

- [x] Refactor scraper with modular architecture (`config.py`, `parsers.py`, `extractors.py`, `writers.py`, `validation.py`)
- [x] Add CLI arguments (`--edition`, `--no-headless`, `--validate`, `--output-dir`, `--timeout`)
- [x] Add schema validation to scraper pipeline (`--validate` flag)
- [x] Remove dependency on `night_order_data.json` - scrape directly from official source
- [x] Fix Phase 2 click timeout with JavaScript click
- [x] Fix Godfather firstNightReminder (was showing otherNight text)
- [x] Create `character_scraper.py` with Playwright automation
- [x] Create `schema_validator.py`
- [x] Create `data/ATTRIBUTION.md`
