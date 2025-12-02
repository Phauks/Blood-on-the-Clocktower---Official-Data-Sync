# Export JSON Analysis

## Summary

Analyzed two exported JSON files from script.bloodontheclocktower.com:
1. **All Characters.json** - Complete character list (174 characters)
2. **example_script.json** - Sample script (30 characters)

## Key Findings

### Export Format

The export JSON is **NOT full character objects** - it's just an **array of character ID strings**.

**Structure:**
```json
[
  {
    "id": "_meta",
    "author": "Emily",
    "name": "All Characters"
  },
  "steward",
  "knight",
  "chef",
  "washerwoman",
  "imp",
  ...
]
```

**Components:**
1. **First element**: Meta object with script name and author
   - `id: "_meta"` (always)
   - `name`: Script name
   - `author`: Script author

2. **Remaining elements**: Character ID strings
   - Just the character ID (e.g., "washerwoman", "imp", "balloonist")
   - No additional data (ability, team, night order, etc.)

## Total Character Count

**174 official characters** (from "All Characters.json")

**Matches HAR analysis**: 175 icons found (1 icon difference likely due to variant/alternate art)

## Sample Character IDs

### Townsfolk (sample):
- steward, knight, chef, noble, investigator, washerwoman, clockmaker, grandmother, librarian, shugenja, pixie, bountyhunter, empath, highpriestess, sailor, balloonist, general, preacher, chambermaid

### Outsider (sample):
- butler, drunk, recluse, sweetheart, tinker, saint, klutz, barber, mutant, damsel, heretic, golem, lunatic, goon, moonchild, politician, snitch, plaguedoctor, puzzlemaster

### Minion (sample):
- mezepheles, godfather, spy, cerenovus, devilsadvocate, poisoner, assassin, widow, pithag, scarletwoman, boomdandy, organgrinder, fearmonger, marionette

### Demon (sample):
- imp, vigormortis, fanggu, nodashii, vortox, pukka, shabaloth, zombuul, po, lleech, alhadikhia, legion

### Traveller (sample):
- beggar, bureaucrat, thief, gunslinger, scapegoat, barista, harlot, butcher, bonecollector, deviant, apprentice, matron, judge, bishop, voudon, gangster

### Fabled (sample):
- doomsayer, angel, buddhist, hellslibrarian, revolutionary, fiddler, toymaker, fibbin, duchess, sentinel, spiritofivory, djinn, stormcatcher, ferryman, deusexfiasco, gardener, bootlegger

## Implications for Scraping

### ✅ What We Can Get from Export

1. **Complete list of character IDs** (174 characters)
2. **Script metadata** (name, author)
3. **Character order** in scripts

### ❌ What We CANNOT Get from Export

1. **Character abilities** - Not in export
2. **Team assignments** - Not in export
3. **Edition information** - Not in export
4. **Night order numbers** - Not in export
5. **Reminders** - Not in export
6. **Flavor text** - Not in export
7. **Setup flags** - Not in export
8. **Jinxes** - Not in export

### ⚠️ Critical Insight

**The export function only gives us character IDs, not full character data!**

This means:
- We **cannot** use the export function to get complete character information
- We **must** scrape character data from the DOM or extract from JavaScript
- The export is useful for getting a **complete character ID list** to validate our scraping

## Scraping Strategy - Updated

### Phase 1: Get Character ID List

**Option A: Use Export (Easiest)**
1. Use Playwright to automate export of "All Characters"
2. Parse JSON to get complete character ID list
3. Use as master list for validation

**Option B: Scrape Character List**
1. Extract character IDs from DOM
2. Validate against known list

**Recommendation**: Use Option A - automate the export to get the definitive list

### Phase 2: Extract Character Data

**Must use DOM scraping or JavaScript extraction**

**Approach 1: DOM Scraping**
```python
# For each character:
1. Click/hover on character card
2. Extract:
   - Name
   - Team (from CSS class or data attribute)
   - Ability text
   - Edition (from folder path or data attribute)
3. Determine alignment suffix for icon URL
```

**Approach 2: JavaScript Context Extraction**
```python
# Try to access character data from JavaScript
character_data = page.evaluate('''() => {
    // Look for global character data
    // May be in window.characterData, app state, etc.
    return window.getAllCharacterData();
}''')
```

**Recommendation**: Try Approach 2 first (faster), fall back to Approach 1

### Phase 3: Download Icons

Once we have character data with editions and teams:

```python
def get_icon_url(char_id, edition, team):
    base = "https://script.bloodontheclocktower.com/src/assets/icons"

    # Determine suffix based on team
    if team in ['townsfolk', 'outsider']:
        suffix = '_g'
    elif team in ['minion', 'demon']:
        suffix = '_e'
    else:  # traveller, fabled
        suffix = ''

    return f"{base}/{edition}/{char_id}{suffix}.webp"

# Download directly - no scraping needed for icons!
```

## Example Script Analysis

**example_script.json** contains 30 characters:

```
Meta: "Catfishing" by Emily
Characters:
- chef, investigator, grandmother, balloonist, snakecharmer
- dreamer, fortuneteller, gambler, savant, philosopher
- cannibal, amnesiac, ravenkeeper, lunatic, drunk
- recluse, sweetheart, mutant, godfather, cerenovus
- pithag, widow, imp, vigormortis, fanggu
```

**Mixed editions** (TB, BMR, SNV, Carousel) - confirms characters from multiple editions can be in one script

## Next Steps

### Immediate Actions

1. **Inspect DOM structure**
   - Open script.bloodontheclocktower.com
   - Open DevTools → Elements
   - Find a character card in the sidebar
   - Document:
     - CSS selectors for character elements
     - Data attributes (data-id, data-team, etc.)
     - Where ability text is displayed

2. **Test JavaScript console**
   ```javascript
   // Try these in browser console:
   window
   document.querySelector('[data-character-id]')
   // Look for character data in app state
   ```

3. **Inspect character detail view**
   - Click on a character
   - See if full details appear
   - Check if we can scrape from detail view

### Implementation Priority

1. ✅ **Character ID list** - Can get from export (done)
2. ⏳ **Character data** - Need DOM inspection (pending)
3. ✅ **Icon URLs** - Pattern known, can construct (ready)
4. ✅ **Icon download** - Direct download (ready)

## Data Completeness Check

**From HAR Analysis**: 175 icon URLs found
**From Export**: 174 character IDs exported

**1 missing character** - possibilities:
- One character has alternate art (2 icons, 1 ID)
- One experimental character not in export but has icon
- Icon for deleted/renamed character

**Action**: Compare HAR icon list vs export ID list to find discrepancy

## Conclusion

**Export function is useful but limited:**
- ✅ Gives complete character ID list (174 characters)
- ❌ Does NOT give character data (abilities, teams, etc.)

**We still need to:**
1. Scrape or extract full character data from website
2. Download icons using known URL pattern
3. Match character IDs to their full data

**Next investigation needed:**
- DOM structure for character cards
- JavaScript variables containing character data
- Best extraction method for abilities, teams, night order, etc.
