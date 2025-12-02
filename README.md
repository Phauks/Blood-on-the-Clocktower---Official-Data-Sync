# Blood on the Clocktower - Official Data Sync

Automatically syncs official Blood on the Clocktower character data from the [official script tool](https://script.bloodontheclocktower.com/) and [wiki](https://wiki.bloodontheclocktower.com/), then publishes versioned releases for community tools.

## Features

- **Complete Character Data**: All 174+ characters with abilities, teams, editions, night order, and jinxes
- **Reminder Tokens**: Extracted from wiki "How to Run" sections
- **Character Icons**: WebP images downloaded from the official script tool
- **Incremental Updates**: Only fetches new/changed data to minimize requests
- **Versioned Releases**: Daily automated releases with content hashing for update checking

## Quick Start

### For Token Generator Users

Download the latest release ZIP from [Releases](../../releases). It contains:
- `characters.json` - All character data with local image paths
- `manifest.json` - Version info and content hash for update checking
- `icons/` - Character icon images (WebP format)

### For Developers

```bash
# Clone the repository
git clone https://github.com/Phauks/Blood-on-the-Clocktower---Official-Data-Sync.git
cd Blood-on-the-Clocktower---Official-Data-Sync

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run full pipeline (scrape + validate + images + reminders + package)
python src/scrapers/character_scraper.py --all

# Or run individual steps
python src/scrapers/character_scraper.py              # Scrape character data
python src/scrapers/character_scraper.py --images     # Download icons
python src/scrapers/character_scraper.py --reminders  # Fetch reminder tokens
python src/scrapers/character_scraper.py --package    # Create dist/ package
```

## Output Structure

```
dist/                           # Distribution package (for releases)
├── characters.json             # All characters (clean, no internal fields)
├── manifest.json               # Version, content hash, edition index
└── icons/{edition}/{id}.webp   # Character icons

data/                           # Working data (for development)
├── characters/{edition}/       # Individual character JSON files
├── characters/all_characters.json
└── manifest.json
```

## Character Data Format

```json
{
  "id": "washerwoman",
  "name": "Washerwoman",
  "edition": "tb",
  "team": "townsfolk",
  "ability": "You start knowing that 1 of 2 players is a particular Townsfolk.",
  "image": "icons/tb/washerwoman.webp",
  "firstNight": 32,
  "firstNightReminder": "Show the character token of a Townsfolk in play...",
  "otherNight": 0,
  "otherNightReminder": "",
  "setup": false,
  "reminders": ["TOWNSFOLK", "WRONG"],
  "remindersGlobal": [],
  "jinxes": []
}
```

## Update Checking

The `manifest.json` includes fields for update checking:

```json
{
  "schemaVersion": 1,
  "version": "2025.12.02",
  "contentHash": "abc123...",
  "total_characters": 174,
  "editions": { "tb": [...], "bmr": [...], ... }
}
```

See [`examples/update_checker.py`](examples/update_checker.py) for a complete implementation.

## CLI Options

```
--all, -a           Run full pipeline (validate + images + reminders + package)
--edition, -e       Only scrape specific editions (tb, bmr, snv, etc.)
--images, -i        Download character icons
--reminders, -r     Fetch reminder tokens from wiki
--package, -p       Create distribution package in dist/
--validate          Run schema validation
--no-headless       Show browser window (debugging)
-v                  Verbose output
```

## Editions

| Edition | Code | Characters |
|---------|------|------------|
| Trouble Brewing | `tb` | 27 |
| Bad Moon Rising | `bmr` | 30 |
| Sects & Violets | `snv` | 30 |
| Unreleased (Carousel) | `carousel` | 68 |
| Fabled | `fabled` | 13 |
| Loric | `loric` | 6 |

## Data Sources

- **Character Data**: [Official Script Tool](https://script.bloodontheclocktower.com/)
- **Reminder Tokens**: [Official Wiki](https://wiki.bloodontheclocktower.com/)

## License

MIT License - See [LICENSE](LICENSE) for details.

Data sourced from official Blood on the Clocktower resources. See [ATTRIBUTION.md](ATTRIBUTION.md) for details.