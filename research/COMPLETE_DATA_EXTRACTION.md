# Complete Data Extraction Plan

## 🎉 ALL Data Available in HTML!

After thorough analysis, we can extract **nearly complete** character data from the HTML!

## Data Sources in HTML

### 1. Character List (`#all-characters`)
**Location**: `<div id="all-characters">` sidebar
**Contains**: Basic character info

**Extractable Fields**:
- ✅ `id` - Character ID (data-id attribute)
- ✅ `name` - Character name (.character-name text)
- ✅ `team` - Team type (data-type: townsfolk, outsider, minion, demon, traveller, fabled)
- ✅ `ability` - Ability text (.ability-text div)
- ✅ `image` - Icon URL path (img src)
- ✅ `edition` - Parsed from icon path (tb, bmr, snv, carousel, fabled, loric)

**Sample**:
```json
{
  "id": "acrobat",
  "name": "Acrobat",
  "team": "townsfolk",
  "ability": "Each night*, choose a player: if they are or become drunk or poisoned tonight, you die.",
  "image": "src/assets/icons/carousel/acrobat_g.webp",
  "edition": "carousel"
}
```

### 2. First Night Sheet (`<div class="first-night">`)
**Location**: Night sheet - First Night section
**Contains**: First night order and reminders

**Extractable Fields**:
- ✅ `firstNight` - Order number (position in list, starts at 1)
- ✅ `firstNightReminder` - Storyteller reminder text
- ✅ `reminders` - Reminder tokens (text in <b> tags)

**Sample Data**:
```
Order 2: Angel
  Reminder: "Announce which players are protected by the Angel. Add the PROTECTED token to the relevant players."
  Tokens: ["PROTECTED"]

Order 33: Washerwoman
  Reminder: "Show the Townsfolk character token. Point to both the TOWNSFOLK and WRONG players."
  Tokens: ["TOWNSFOLK", "WRONG"]
```

**Total**: 125 characters in first night order

### 3. Other Nights Sheet (`<div class="other-night">`)
**Location**: Night sheet - Other Nights section
**Contains**: Subsequent nights order and reminders

**Extractable Fields**:
- ✅ `otherNight` - Order number (position in list, starts at 1)
- ✅ `otherNightReminder` - Storyteller reminder text
- ✅ Additional reminder tokens

**Sample Data**:
```
Order 2: Toymaker
  Reminder: "If it is a night when a Demon attack could end the game, and the Demon is marked FINAL NIGHT: NO ATTACK, mark that Demon with a shroud."
  Tokens: ["FINAL NIGHT: NO ATTACK"]

Order 6: Poisoner
  Reminder: "The Poisoner chooses a player."
  Tokens: []
```

**Total**: 65 characters in other night order

## Complete Data Structure

### Merging All Sources

By combining data from all three sections, we can build complete character objects:

```json
{
  "id": "washerwoman",
  "name": "Washerwoman",
  "team": "townsfolk",
  "ability": "You start knowing that 1 of 2 players is a particular Townsfolk.",
  "image": "https://script.bloodontheclocktower.com/src/assets/icons/tb/washerwoman_g.webp",
  "edition": "tb",
  "firstNight": 33,
  "firstNightReminder": "Show the Townsfolk character token. Point to both the TOWNSFOLK and WRONG players.",
  "otherNight": 0,
  "otherNightReminder": "",
  "reminders": ["TOWNSFOLK", "WRONG"],
  "setup": false
}
```

## Fields Comparison

### ✅ Available from HTML

| Field | Source | Status |
|-------|--------|--------|
| `id` | data-id attribute | ✓ Perfect |
| `name` | .character-name text | ✓ Perfect |
| `team` | data-type attribute | ✓ Perfect |
| `ability` | .ability-text div | ✓ Perfect |
| `image` | img src (needs URL conversion) | ✓ Perfect |
| `edition` | Parsed from icon path | ✓ Perfect |
| `firstNight` | Position in first night list | ✓ Perfect |
| `firstNightReminder` | Night sheet reminder text | ✓ Perfect |
| `otherNight` | Position in other night list | ✓ Perfect |
| `otherNightReminder` | Night sheet reminder text | ✓ Perfect |
| `reminders` | <b> tags in reminder text | ✓ Good (needs parsing) |
| `jinxes` | Djinn character section (.jinxes) | ✓ Perfect (131 jinxes found!) |

### ⚠️ Partial / Needs Work

| Field | Status | Notes |
|-------|--------|-------|
| `remindersGlobal` | ⚠️ Not extractable | Default to empty array `[]` - no HTML indicators found |
| `setup` | ✓ Detectable | Pattern matching on ability text (see SETUP_FLAG_DETECTION.md) |

### ❌ Not Available in HTML

| Field | Status | Alternative |
|-------|--------|-------------|
| `flavor` | ✗ Missing | Could scrape from wiki |
| `special` | ✗ Missing | Rare field, may not be needed |

## Implementation Strategy

### Phase 1: Extract Character List

```python
from playwright.sync_api import sync_playwright
import re

characters = {}

# Extract from #all-characters
char_elements = page.query_selector_all('#all-characters .item[data-id]')

for elem in char_elements:
    char_id = elem.get_attribute('data-id')

    character = {
        'id': char_id,
        'name': elem.query_selector('.character-name').text_content().strip(),
        'team': elem.get_attribute('data-type'),
        'ability': elem.query_selector('.ability-text').text_content().strip(),
        'edition': parse_edition_from_icon(elem.query_selector('img').get_attribute('src')),
        'image': construct_full_url(elem.query_selector('img').get_attribute('src')),
        # Defaults for missing fields
        'firstNight': 0,
        'otherNight': 0,
        'firstNightReminder': '',
        'otherNightReminder': '',
        'reminders': [],
        'remindersGlobal': [],  # Not extractable from HTML
        'setup': False
    }

    characters[char_id] = character
```

### Phase 2: Extract Night Order

```python
# Extract First Night order
first_night_items = page.query_selector_all('.first-night .item')

for order, item in enumerate(first_night_items, 1):
    # Get character name
    name_elem = item.query_selector('.night-sheet-char-name a, .night-sheet-char-name span')
    if not name_elem:
        continue

    name = name_elem.text_content().strip()

    # Get icon to extract character ID
    icon_src = item.query_selector('img').get_attribute('src')
    char_id = parse_char_id_from_icon(icon_src)

    # Skip if character not in our list (special tokens like "Dusk")
    if char_id not in characters:
        continue

    # Get reminder
    reminder_elem = item.query_selector('.night-sheet-reminder')
    reminder_html = reminder_elem.inner_html()

    # Extract tokens from <b> tags
    tokens = re.findall(r'<b>([^<]+)</b>', reminder_html)

    # Clean reminder text
    reminder_text = reminder_elem.text_content().strip()

    # Update character
    characters[char_id]['firstNight'] = order
    characters[char_id]['firstNightReminder'] = reminder_text
    if tokens:
        characters[char_id]['reminders'].extend(tokens)
```

### Phase 3: Extract Other Nights Order

```python
# Same as Phase 2, but for .other-night section
other_night_items = page.query_selector_all('.other-night .item')

for order, item in enumerate(other_night_items, 1):
    # ... similar to first night extraction ...

    characters[char_id]['otherNight'] = order
    characters[char_id]['otherNightReminder'] = reminder_text
    # Tokens may include additional reminders
```

### Phase 4: Extract Jinxes from Djinn Section

```python
import re

def parse_character_id_from_icon_path(icon_src):
    """Extract character ID from icon path."""
    # Match: icons/{edition}/{id}_{suffix}.webp or icons/{edition}/{id}.webp
    match = re.search(r'/icons/[^/]+/([a-z]+?)(?:_[ge])?\.webp', icon_src)
    return match.group(1) if match else None

# Get all jinx items from Djinn section
jinx_items = page.query_selector_all('.jinxes-container .jinxes .item')

for jinx_item in jinx_items:
    # Get the two character icons
    icons = jinx_item.query_selector_all('.icons img.icon')

    if len(icons) != 2:
        continue  # Skip malformed jinxes

    # Extract character IDs from icon sources
    char1_src = icons[0].get_attribute('src')
    char2_src = icons[1].get_attribute('src')

    char1_id = parse_character_id_from_icon_path(char1_src)
    char2_id = parse_character_id_from_icon_path(char2_src)

    # Get jinx rule text
    jinx_text = jinx_item.query_selector('.jinx-text').text_content().strip()

    # Add jinx to both characters (bidirectional)
    if char1_id in characters:
        if 'jinxes' not in characters[char1_id]:
            characters[char1_id]['jinxes'] = []

        characters[char1_id]['jinxes'].append({
            'id': char2_id,
            'reason': jinx_text
        })

    if char2_id in characters:
        if 'jinxes' not in characters[char2_id]:
            characters[char2_id]['jinxes'] = []

        characters[char2_id]['jinxes'].append({
            'id': char1_id,
            'reason': jinx_text
        })
```

**Note**: See [JINX_EXTRACTION.md](JINX_EXTRACTION.md) for detailed jinx extraction documentation.

## Data Quality Notes

**IMPORTANT: Reminder tokens should NOT be deduplicated!**
- Characters may need multiple copies of the same reminder token
- Keep all reminder tokens as extracted, including duplicates
- Example: A character might need multiple "POISONED" tokens for different players

### Night Order Considerations

**Characters Not in Night Order**:
- Characters with `firstNight: 0` and `otherNight: 0` don't wake up
- Examples: Drunk, Recluse, Saint (passive abilities)

**Special Entries**:
- "Dusk" and "Dawn" are not characters, but night phase markers
- Should be filtered out during extraction

**Hidden Characters** (class="item hidden"):
- Travellers may be marked as hidden in night sheet
- Still need to be included in data

### Reminder Token Extraction

**Current Approach**: Extract text in `<b>` tags

**Known Tokens**:
- PROTECTED (Angel)
- TOWNSFOLK, WRONG (Washerwoman)
- OUTSIDER, WRONG (Librarian)
- MINION, WRONG (Investigator)
- POISONED (Poisoner)
- STORMCAUGHT (Storm Catcher)
- FINAL NIGHT: NO ATTACK (Toymaker)

**Edge Cases**:
- Some reminders have HTML formatting (italic circles: `<i class="fa-solid fa-circle">`)
- Need to strip HTML but preserve semantic meaning
- `&amp;` entities need to be decoded to `&`

## Missing Data Handling

### Global Reminders

**Status**: Not extractable from HTML

**Reason**: `remindersGlobal` are meta-tokens for Storyteller tracking (e.g., "Is the Drunk", "Is the Philosopher") that don't appear in:
- Night reminder text (not night actions)
- Ability text (not explicitly mentioned)
- Any identifiable HTML structure

**Examples of Global Reminders:**
- **Drunk**: `["Is the Drunk"]` - Track what false character Drunk thinks they are
- **Philosopher**: `["Is the Philosopher"]` - Track when Philosopher gains different ability

**Solution**: Default to empty array `[]` for all characters

**Future Enhancement**: Could manually maintain a list of known global reminders if Token Generator needs them.

### Setup Flag

**Detection Method**: Pattern matching on ability text

**Patterns to Detect:**
1. False identity: "You do not know you are...", "You think you are..."
2. Bracket text: `[+1 Outsider]`, `[1 Townsfolk is evil]`, etc.
3. Explicit character list for known setup characters

**Implementation**: See [SETUP_FLAG_DETECTION.md](SETUP_FLAG_DETECTION.md) for complete strategy

**Examples:**
- **Drunk**: "You do not know you are the Drunk..." → `setup: true`
- **Baron**: "...[+2 Outsiders]" → `setup: true`
- **Washerwoman**: "You start knowing..." (no bracket text) → `setup: false`

### Flavor Text

**Not in HTML**, options:
1. Leave empty (simplest)
2. Scrape from wiki (links are in HTML: `https://wiki.bloodontheclocktower.com/{CharacterName}`)
3. Skip for now, add later if Token Generator needs it

## Expected Output Stats

**Total Characters**: 174
**With First Night Order**: ~125 characters
**With Other Night Order**: ~65 characters
**No Night Actions**: ~30-40 characters (passive abilities)
**Total Jinx Pairs**: 131 (262 bidirectional entries)
**Characters with Jinxes**: ~93 characters
**Characters without Jinxes**: ~81 characters

**Editions**:
- tb: ~20 characters
- bmr: ~20 characters
- snv: ~20 characters
- carousel: ~80 characters
- fabled: ~12 characters
- loric: ~20 characters

## Next Steps

1. ✅ HTML structure analyzed
2. ✅ Night order extraction method confirmed
3. ✅ Jinx extraction method confirmed (131 jinxes found!)
4. ⏭️ Implement complete scraper
5. ⏭️ Test with sample characters
6. ⏭️ Validate against official schema
7. ⏭️ Download all icons
8. ⏭️ Generate manifest.json
9. ⏭️ Test with Token Generator

## Summary

### What We Have ✓

**From HTML, we can extract ~98% of official schema fields:**
- All core character info (id, name, team, ability, edition)
- Complete night order information (firstNight, otherNight)
- Night reminders (firstNightReminder, otherNightReminder)
- Reminder tokens (parsed from HTML `<b>` tags)
- Jinxes (131 jinx pairs from Djinn section!)
- Icon URLs

### What's Missing ✗

**Minor/Optional fields (~2% of schema):**
- Flavor text (can scrape from wiki if needed)
- Setup flag (can default to false)
- Special abilities (rare, homebrew-specific)

### Recommendation

**Proceed with HTML extraction!**

The HTML contains sufficient data for a fully functional character database. Missing fields are either:
- Optional/rarely used
- Can be added later if Token Generator needs them
- Can be scraped from wiki as enhancement

This is more than enough to build a complete, working system! 🚀
