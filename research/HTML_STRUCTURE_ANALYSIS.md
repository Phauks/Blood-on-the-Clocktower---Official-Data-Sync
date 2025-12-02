# HTML Structure Analysis - COMPLETE

## 🎯 SUCCESS! Character Data Found in HTML

The HTML contains **ALL character data** we need!

## Character HTML Structure

### Location
```html
<div id="all-characters">
  <!-- 174 character items here -->
</div>
```

### Individual Character Element

```html
<div class="item selected"
     data-id="acrobat"
     data-team="good"
     data-type="townsfolk"
     tabindex="0">
  <img class="icon" src="src/assets/icons/carousel/acrobat_g.webp">
  <div class="character-name">Acrobat</div>
  <div class="button">
    <button type="button" title="Show/hide character ability">
      <i class="fa-solid fa-chevron-down"></i>
    </button>
  </div>
  <div class="ability-text nodisplay">
    Each night*, choose a player: if they are or become drunk or poisoned tonight, you die.
  </div>
</div>
```

## Extractable Data Fields

### ✅ From HTML Attributes

| Field | Source | Example |
|-------|--------|---------|
| **Character ID** | `data-id` | `"acrobat"` |
| **Alignment** | `data-team` | `"good"` or `"evil"` |
| **Team Type** | `data-type` | `"townsfolk"`, `"outsider"`, `"minion"`, `"demon"`, `"traveller"`, `"fabled"` |
| **Character Name** | `.character-name` text | `"Acrobat"` |
| **Ability** | `.ability-text` text | `"Each night*, choose a player..."` |
| **Icon Path** | `img src` | `"src/assets/icons/carousel/acrobat_g.webp"` |
| **Edition** | Parsed from icon path | `"carousel"` (from `/carousel/`) |
| **Icon Suffix** | Parsed from icon filename | `"_g"` (from `acrobat_g.webp`) |

## Sample Extraction Results

**Found 174 characters** in HTML (perfect match with export JSON!)

### Sample by Team Type:

**Townsfolk (good):**
- **Acrobat** (carousel)
  - Ability: "Each night*, choose a player: if they are or become drunk or poisoned tonight, you die."
  - Icon: `src/assets/icons/carousel/acrobat_g.webp`

**Outsider (good):**
- **Barber** (snv)
  - Ability: "If you died today or tonight, the Demon may choose 2 players (not another Demon) to swap characters."
  - Icon: `src/assets/icons/snv/barber_g.webp`

**Minion (evil):**
- **Assassin** (bmr)
  - Ability: "Once per game, at night*, choose a player: they die, even if for some reason they could not."
  - Icon: `src/assets/icons/bmr/assassin_e.webp`

**Demon (evil):**
- **Al-Hadikhia** (carousel)
  - Ability: "Each night*, you may choose 3 players (all players learn who): each silently chooses to live or die,..."
  - Icon: `src/assets/icons/carousel/alhadikhia_e.webp`

## CSS Selectors for Scraping

### Get All Characters
```css
#all-characters .item[data-id]
```

### Character Data Extraction
```python
# For each character element:
character_id = element.get_attribute('data-id')
team_alignment = element.get_attribute('data-team')  # good/evil
team_type = element.get_attribute('data-type')       # townsfolk/minion/etc
name = element.query_selector('.character-name').text_content()
ability = element.query_selector('.ability-text').text_content()
icon_src = element.query_selector('img.icon').get_attribute('src')

# Parse edition from icon path
# "src/assets/icons/carousel/acrobat_g.webp" -> "carousel"
import re
match = re.search(r'/icons/([^/]+)/', icon_src)
edition = match.group(1) if match else 'unknown'
```

## Scraping Strategy - FINAL

### ✅ What We Can Extract from HTML

1. **Character ID** ✓
2. **Name** ✓
3. **Team** (townsfolk, outsider, minion, demon, traveller, fabled) ✓
4. **Alignment** (good/evil) ✓
5. **Ability Text** ✓
6. **Edition** (from icon path) ✓
7. **Icon URL** ✓

### ❌ What's Still Missing

The following fields from the official schema are NOT in the HTML:
- **firstNight** (night order number)
- **firstNightReminder** (storyteller reminder)
- **otherNight** (other nights order)
- **otherNightReminder** (storyteller reminder)
- **reminders** (reminder tokens)
- **remindersGlobal** (global reminders)
- **setup** (affects setup)
- **flavor** (flavor text)
- **jinxes** (jinx interactions)
- **special** (special abilities)

### 🎯 Where to Get Missing Data

**Option 1: Official Wiki Scraping**
- Each character has wiki link: `https://wiki.bloodontheclocktower.com/{CharacterName}`
- Could scrape from there (but adds complexity)

**Option 2: Use Partial Data**
- Export what we have (id, name, team, ability, edition, image)
- Add placeholder values for missing fields
- Token Generator might not need all fields

**Option 3: Find Full Data in JavaScript**
- The complete character objects with all fields might be in the JavaScript bundle
- Would need to extract and parse the minified JS

**Recommendation**: Start with Option 2 (partial data), validate it works for Token Generator, then enhance if needed

## Implementation Plan

### Phase 1: Basic Scraper (Recommended Start)

```python
from playwright.sync_api import sync_playwright
import json
import re

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('https://script.bloodontheclocktower.com/')

    # Wait for characters to load
    page.wait_for_selector('#all-characters .item[data-id]')

    # Get all character elements
    characters = page.query_selector_all('#all-characters .item[data-id]')

    character_data = []

    for char_element in characters:
        # Extract data
        char_id = char_element.get_attribute('data-id')
        team_alignment = char_element.get_attribute('data-team')
        team_type = char_element.get_attribute('data-type')

        name = char_element.query_selector('.character-name').text_content().strip()
        ability = char_element.query_selector('.ability-text').text_content().strip()
        icon_src = char_element.query_selector('img.icon').get_attribute('src')

        # Parse edition from icon path
        edition_match = re.search(r'/icons/([^/]+)/', icon_src)
        edition = edition_match.group(1) if edition_match else 'unknown'

        # Construct full icon URL
        icon_filename = icon_src.split('/')[-1]
        icon_url = f"https://script.bloodontheclocktower.com/{icon_src}"

        # Build character object
        character = {
            "id": char_id,
            "name": name,
            "team": team_type,
            "ability": ability,
            "image": icon_url,
            "edition": edition,
            # Optional: Add placeholders for missing fields
            "firstNight": 0,
            "otherNight": 0,
            "reminders": [],
            "setup": False
        }

        character_data.append(character)
        print(f"Extracted: {name} ({edition}/{team_type})")

    # Save to file
    with open('characters_scraped.json', 'w') as f:
        json.dump(character_data, f, indent=2)

    print(f"\nTotal characters extracted: {len(character_data)}")

    browser.close()
```

### Phase 2: Download Icons

```python
import requests
import os
from pathlib import Path

for character in character_data:
    edition = character['edition']
    char_id = character['id']
    icon_url = character['image']

    # Determine suffix from team
    if character['team'] in ['townsfolk', 'outsider']:
        suffix = '_g'
    elif character['team'] in ['minion', 'demon']:
        suffix = '_e'
    else:
        suffix = ''

    # Create directory
    icon_dir = Path(f'data/icons/{edition}')
    icon_dir.mkdir(parents=True, exist_ok=True)

    # Download icon
    icon_filename = f'{char_id}{suffix}.webp'
    icon_path = icon_dir / icon_filename

    response = requests.get(icon_url)
    with open(icon_path, 'wb') as f:
        f.write(response.content)

    print(f"Downloaded: {icon_path}")
```

### Phase 3: Save Individual Character Files

```python
from pathlib import Path
import json

for character in character_data:
    edition = character['edition']
    char_id = character['id']

    # Create directory
    char_dir = Path(f'data/characters/{edition}')
    char_dir.mkdir(parents=True, exist_ok=True)

    # Update image URL to GitHub raw URL
    # (will do this after upload to GitHub)

    # Save character JSON
    char_path = char_dir / f'{char_id}.json'
    with open(char_path, 'w') as f:
        json.dump(character, f, indent=2)

    print(f"Saved: {char_path}")
```

## Summary

### ✅ HTML Analysis Complete!

**Total Characters**: 174
**Data Available**: id, name, team, ability, edition, icon URL
**Missing Data**: night order, reminders, setup flags, jinxes, flavor

**Extraction Method**: Playwright DOM scraping
**Difficulty**: Easy - all data in HTML attributes and text
**Time to Implement**: ~1 hour for basic scraper

### Next Steps

1. ✅ Analysis complete
2. ⏭️ Implement basic Playwright scraper
3. ⏭️ Download all 174 character icons
4. ⏭️ Generate character JSON files
5. ⏭️ Create manifest.json
6. ⏭️ Test with Token Generator
7. ⏭️ Enhance with missing data if needed

**Ready to start implementation!** 🚀
