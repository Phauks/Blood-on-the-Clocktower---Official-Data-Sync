# Jinx Extraction Strategy

## Overview

Jinxes are special interaction rules between character pairs that resolve conflicts or contradictions in their abilities. On the official script tool, **all jinxes are displayed under the Djinn character** (a Fabled character whose ability is to define special rules).

**Total Jinxes Found**: 131

## HTML Structure

### Container Hierarchy

```html
<div class="fabled-and-loric-container">
  <div class="fabled-and-loric">
    <div class="jinxes-container">
      <!-- Djinn character header -->
      <div class="jinxes-heading">
        <div class="icon-container">
          <img class="icon" src="src/assets/icons/fabled/djinn.webp">
        </div>
        <div class="name-and-summary">
          <h3 class="character-name">Djinn</h3>
          <div class="character-summary">Use the Djinn's special rule...</div>
        </div>
      </div>

      <!-- Jinx list -->
      <div nitems="131" class="jinxes">
        <!-- Individual jinx items -->
      </div>
    </div>
  </div>
</div>
```

### Individual Jinx Item Structure

```html
<div id="bountyhunter-philosopher-jinx" class="item">
  <div class="icons">
    <img id="bountyhunter-icon-jinxes" class="icon" src="src/assets/icons/carousel/bountyhunter_g.webp">
    <img id="philosopher-icon-jinxes" class="icon" src="src/assets/icons/snv/philosopher_g.webp">
  </div>
  <div class="jinx-text">
    If the Philosopher gains the Bounty Hunter ability, a Townsfolk might turn evil.
  </div>
</div>
```

## CSS Selectors for Extraction

### Get all jinxes
```css
.jinxes-container .jinxes .item
```

### Get character icons for a jinx
```css
.jinxes .item .icons img.icon
```

### Get jinx rule text
```css
.jinxes .item .jinx-text
```

## Extraction Implementation

### Python + Playwright Approach

```python
# Get all jinx items
jinx_items = page.query_selector_all('.jinxes-container .jinxes .item')

jinxes_list = []

for jinx_item in jinx_items:
    # Get the two character icons
    icons = jinx_item.query_selector_all('.icons img.icon')

    if len(icons) != 2:
        continue  # Skip malformed jinxes

    # Extract character IDs from icon sources
    char1_src = icons[0].get_attribute('src')
    char2_src = icons[1].get_attribute('src')

    # Parse character IDs from paths
    # Example: "src/assets/icons/carousel/bountyhunter_g.webp" -> "bountyhunter"
    char1_id = parse_character_id_from_path(char1_src)
    char2_id = parse_character_id_from_path(char2_src)

    # Get jinx rule text
    jinx_text_elem = jinx_item.query_selector('.jinx-text')
    jinx_text = jinx_text_elem.text_content().strip()

    # Create jinx object
    jinx = {
        "id": char2_id,  # The character being jinxed
        "reason": jinx_text
    }

    # Store with first character as key
    jinxes_list.append({
        "character": char1_id,
        "jinx": jinx
    })

# Group jinxes by character
jinxes_by_character = {}
for item in jinxes_list:
    char_id = item["character"]
    if char_id not in jinxes_by_character:
        jinxes_by_character[char_id] = []
    jinxes_by_character[char_id].append(item["jinx"])
```

### Helper Function: Parse Character ID from Icon Path

```python
import re

def parse_character_id_from_path(icon_src):
    """
    Extract character ID from icon path.

    Examples:
      "src/assets/icons/carousel/bountyhunter_g.webp" -> "bountyhunter"
      "src/assets/icons/snv/philosopher_g.webp" -> "philosopher"
      "src/assets/icons/tb/spy_e.webp" -> "spy"
      "src/assets/icons/fabled/djinn.webp" -> "djinn"
    """
    # Match pattern: icons/{edition}/{id}_{suffix}.webp or icons/{edition}/{id}.webp
    match = re.search(r'/icons/[^/]+/([a-z]+?)(?:_[ge])?\.webp', icon_src)

    if match:
        return match.group(1)

    return None
```

## Data Structure in Official Schema

According to the official schema, jinxes are stored as an array on each character:

```json
{
  "id": "widow",
  "name": "Widow",
  "team": "minion",
  "jinxes": [
    {
      "id": "alchemist",
      "reason": "If the Widow sees the Alchemist, the Alchemist is poisoned."
    },
    {
      "id": "magician",
      "reason": "When the Spy sees the Grimoire, the Demon and Magician's character tokens are removed."
    }
  ]
}
```

## Mapping Jinxes to Characters

Since jinxes involve **two characters**, we need to decide which character gets which jinx:

### Approach 1: Both Characters Get the Jinx (Recommended)

Store the same jinx on both characters, but from their perspective:

**Character 1 (Widow)**:
```json
{
  "id": "widow",
  "jinxes": [
    {
      "id": "alchemist",
      "reason": "If the Widow sees the Alchemist, the Alchemist is poisoned."
    }
  ]
}
```

**Character 2 (Alchemist)**:
```json
{
  "id": "alchemist",
  "jinxes": [
    {
      "id": "widow",
      "reason": "If the Widow sees the Alchemist, the Alchemist is poisoned."
    }
  ]
}
```

**Benefits:**
- Each character JSON is self-contained
- Easy to look up jinxes for a specific character
- Matches how players would search ("What are Widow's jinxes?")

**Drawbacks:**
- Data duplication (each jinx stored twice)
- Need to ensure both copies stay in sync

### Approach 2: First Character Only (Simpler)

Store each jinx only on the first character in the alphabetical pair:

**Only on Alchemist** (comes before Widow alphabetically):
```json
{
  "id": "alchemist",
  "jinxes": [
    {
      "id": "widow",
      "reason": "If the Widow sees the Alchemist, the Alchemist is poisoned."
    }
  ]
}
```

**Benefits:**
- No data duplication
- Single source of truth

**Drawbacks:**
- Harder to find all jinxes for a character (need to search both ways)
- Less intuitive for consumers

**Recommendation**: Use **Approach 1** (both characters) for better usability.

## Special Cases & Edge Cases

### HTML Encoding

Jinx text may contain HTML entities:
- `&amp;` → `&`
- `&lt;` → `<`
- `&gt;` → `>`

**Solution**: Use `.text_content()` instead of `.inner_html()` to get decoded text.

### Malformed Jinxes

Some jinx items might have:
- Only 1 icon (incomplete)
- More than 2 icons (error)
- Missing text

**Solution**: Validate and skip malformed entries:
```python
icons = jinx_item.query_selector_all('.icons img.icon')
if len(icons) != 2:
    print(f"Warning: Skipping malformed jinx with {len(icons)} icons")
    continue
```

### Character ID Parsing

Icon paths follow this pattern:
- Good: `src/assets/icons/{edition}/{id}_g.webp`
- Evil: `src/assets/icons/{edition}/{id}_e.webp`
- Fabled: `src/assets/icons/fabled/{id}.webp`

**Solution**: Regex pattern handles all cases (see helper function above).

## Integration with Character Extraction

### Phase 1: Extract All Characters (as before)

Extract all 174 characters with basic data.

### Phase 2: Extract All Jinxes

Extract all 131 jinxes from Djinn section.

### Phase 3: Map Jinxes to Characters

```python
# After extracting all jinxes
for jinx_pair in jinxes_list:
    char1_id = jinx_pair["character"]
    char2_id = jinx_pair["jinx"]["id"]
    jinx_reason = jinx_pair["jinx"]["reason"]

    # Add jinx to Character 1
    if char1_id in characters:
        if "jinxes" not in characters[char1_id]:
            characters[char1_id]["jinxes"] = []

        characters[char1_id]["jinxes"].append({
            "id": char2_id,
            "reason": jinx_reason
        })

    # Add jinx to Character 2 (same jinx, reversed perspective)
    if char2_id in characters:
        if "jinxes" not in characters[char2_id]:
            characters[char2_id]["jinxes"] = []

        characters[char2_id]["jinxes"].append({
            "id": char1_id,
            "reason": jinx_reason
        })
```

### Phase 4: Save Character JSONs

Each character JSON will now include its jinxes array (or empty array if no jinxes).

## Example Complete Character with Jinxes

```json
{
  "id": "widow",
  "name": "Widow",
  "team": "minion",
  "ability": "You start knowing 1 Townsfolk character token...",
  "image": "https://raw.githubusercontent.com/Phauks/Blood-on-the-Clocktower---Official-Data-Sync/main/data/icons/bmr/widow_e.webp",
  "edition": "bmr",
  "firstNight": 45,
  "firstNightReminder": "Show the Widow a Townsfolk character token.",
  "otherNight": 0,
  "otherNightReminder": "",
  "reminders": ["Knows"],
  "remindersGlobal": [],
  "setup": false,
  "jinxes": [
    {
      "id": "alchemist",
      "reason": "The Alchemist can not have the Widow ability."
    },
    {
      "id": "damsel",
      "reason": "Only 1 jinxed character can be in play."
    },
    {
      "id": "heretic",
      "reason": "Only 1 jinxed character can be in play."
    },
    {
      "id": "magician",
      "reason": "When the Spy sees the Grimoire, the Demon and Magician's character tokens are removed."
    },
    {
      "id": "poppygrower",
      "reason": "If the Widow sees the Poppy Grower, the Poppy Grower learns this."
    }
  ]
}
```

## Validation

After extraction, validate:
1. **Total jinxes**: Should have 131 jinx pairs
2. **Character IDs exist**: All jinxed character IDs should be in the character list
3. **Bidirectional**: If Widow has jinx with Alchemist, Alchemist should have jinx with Widow
4. **No duplicates**: No character should have duplicate jinx entries for the same partner

## Expected Statistics

- **131 jinx pairs** → **262 jinx entries** (stored on both characters)
- **~93 unique characters involved in jinxes** (based on wiki data)
- **~81 characters with no jinxes** (174 total - 93 with jinxes)

## Summary

✅ **Jinxes are extractable from HTML!**
- Location: Under Djinn character in `.jinxes-container .jinxes`
- Total: 131 jinx pairs
- Structure: Character icons + rule text
- Storage: Add to both characters' `jinxes` array
- Validation: Ensure bidirectional mapping

This completes the data extraction strategy - we now have **100% of the official schema fields** extractable from the HTML! 🎉
