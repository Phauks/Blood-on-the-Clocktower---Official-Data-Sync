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
  "generated": "2025-12-02T00:00:00Z",
  "lastModified": "2025-12-02T00:00:00Z",
  "contentHash": "abc123...",
  "source": "https://script.bloodontheclocktower.com/",
  "total_characters": 174,
  "total_reminders": 181,
  "total_jinxes": 131,
  "total_flavor": 174,
  "editions": ["tb", "bmr", "snv", "carousel", "fabled", "loric"],
  "edition_counts": { "tb": 27, "bmr": 30, ... },
  "edition_reminders": { "tb": 18, "bmr": 45, ... }
}
```

### Manifest Fields

| Field | Description |
|-------|-------------|
| `schemaVersion` | Data format version (increments on breaking changes) |
| `version` | Date-based version string (YYYY.MM.DD) |
| `generated` | ISO timestamp when data was generated |
| `lastModified` | ISO timestamp of last data modification |
| `contentHash` | SHA256 hash of character data for update checking |
| `source` | Official data source URL |
| `total_characters` | Total number of characters |
| `total_reminders` | Total reminder tokens across all characters |
| `total_jinxes` | Total jinx entries across all characters |
| `total_flavor` | Characters with flavor text |
| `editions` | List of edition codes |
| `edition_counts` | Character count per edition |
| `edition_reminders` | Reminder token count per edition |

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

| Edition | Code | Characters | Reminders |
|---------|------|------------|-----------|
| Trouble Brewing | `tb` | 27 | 18 |
| Bad Moon Rising | `bmr` | 30 | 45 |
| Sects & Violets | `snv` | 30 | 37 |
| Unreleased (Carousel) | `carousel` | 68 | 66 |
| Fabled | `fabled` | 13 | 11 |
| Loric | `loric` | 6 | 4 |
| **Total** | | **174** | **181** |


## Data Sources

- **Character Data**: [Official Script Tool](https://script.bloodontheclocktower.com/)
- **Reminder Tokens**: [Official Wiki](https://wiki.bloodontheclocktower.com/)

## License

MIT License - See [LICENSE](LICENSE) for details.

Data sourced from official Blood on the Clocktower resources. See [ATTRIBUTION.md](ATTRIBUTION.md) for details.