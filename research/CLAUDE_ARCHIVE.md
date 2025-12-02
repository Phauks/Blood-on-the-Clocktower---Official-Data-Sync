# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Automatically sync official Blood on the Clocktower character data and icons from the official script tool. Publishes versioned releases for the Token Generator and community tools.

**Data Source**: https://script.bloodontheclocktower.com/
**Schema**: https://github.com/ThePandemoniumInstitute/botc-release/blob/main/script-schema.json

## Repository Structure

```
src/
  scrapers/           # Playwright-based web scraping
    scraper.py        # Main scraper implementation
  transformers/       # Data transformation utilities  
  validators/         # Schema validation
data/
  characters/{edition}/*.json   # Character JSON files by edition
  icons/{edition}/*.webp        # Character icons by edition
  manifest.json                 # Master index with version info
research/             # Archived investigation documents (reference only)
```

## Key Implementation Details

### Data Extraction (from HTML)
- **Characters**: `#all-characters .item[data-id]` → 174 characters
- **First Night**: `.first-night .item` → order, reminders
- **Other Night**: `.other-night .item` → order, reminders
- **Jinxes**: `.jinxes-container .jinxes .item` → 131 pairs (bidirectional)
- **Icons**: URL pattern `https://script.bloodontheclocktower.com/src/assets/icons/{edition}/{id}{_suffix}.webp`

### Field Coverage
✅ id, name, team, ability, edition, image, firstNight, otherNight, firstNightReminder, otherNightReminder, reminders, jinxes
⚠️ setup (pattern detection), flavor (wiki - on change only), special (bag-duplicate detection)
❌ remindersGlobal (default to `[]`)

### Critical Rules
1. **DO NOT deduplicate reminder tokens** - characters may need multiples
2. **Jinxes are bidirectional** - store on both characters
3. **Flavor text**: Only fetch from wiki when character is new/changed
4. **Setup flag**: Detect via `[...]` brackets or "You think you are..." patterns

### Editions
- `tb` - Trouble Brewing
- `bmr` - Bad Moon Rising  
- `snv` - Sects & Violets
- `carousel` - Experimental characters
- `fabled` - Fabled characters
- `loric` - Loric characters

### Icon Naming
- Good (townsfolk/outsider): `{id}_g.webp`
- Evil (minion/demon): `{id}_e.webp`
- Traveller/Fabled: `{id}.webp`

## Commands

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run scraper
python src/scrapers/scraper.py

# Validate data
python src/validators/validate.py
```

## Research Archive

Investigation documents are in `/research/`. Key reference: `COMPLETE_DATA_EXTRACTION.md`

## Attribution

Blood on the Clocktower © The Pandemonium Institute. See `data/ATTRIBUTION.md`.
