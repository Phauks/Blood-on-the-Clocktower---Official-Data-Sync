# HAR File Analysis Results

## Summary

Analysis of network traffic from script.bloodontheclocktower.com reveals the following:

## Key Findings

### 1. Character Icons - CONFIRMED ✓

**Total Icon Requests:** 179
**Unique Characters:** 175
**Format:** WebP (already optimized - no conversion needed!)

**URL Pattern:**
```
https://script.bloodontheclocktower.com/src/assets/icons/{edition}/{character_name}{_suffix}.webp
```

**Editions Found:**
- `tb` - Trouble Brewing (base edition)
- `bmr` - Bad Moon Rising (base edition)
- `snv` - Sects & Violets (base edition)
- `carousel` - Carousel (experimental characters)
- `fabled` - Fabled characters
- `loric` - Loric characters

**Suffix Patterns:**
- `_g` - Good alignment (townsfolk, outsiders)
- `_e` - Evil alignment (minions, demons)
- *(no suffix)* - Travellers and Fabled characters

**Example URLs:**
```
https://script.bloodontheclocktower.com/src/assets/icons/tb/washerwoman_g.webp
https://script.bloodontheclocktower.com/src/assets/icons/tb/imp_e.webp
https://script.bloodontheclocktower.com/src/assets/icons/bmr/sailor_g.webp
https://script.bloodontheclocktower.com/src/assets/icons/fabled/angel.webp
https://script.bloodontheclocktower.com/src/assets/icons/loric/bootlegger.webp
```

### 2. JavaScript Application

**Main Bundle:** `workspace.4a7a0609.js` (1.65 MB)
**Small Bundle:** `workspace.607bad5f.js` (1.6 KB)

**Application Type:** Single Page Application (SPA)
**Likely Framework:** Vue.js or similar (based on HTML structure)

### 3. Character Data Loading

**Critical Finding:** Character data is NOT loaded via separate JSON endpoint

**Evidence:**
- No `characters.json`, `data.json`, or similar files in network requests
- Character metadata likely embedded in JavaScript bundle (minified/obfuscated)
- Character icons loaded dynamically as user browses

**Implications:**
- Cannot use simple HTTP requests to fetch character data
- Must use browser automation (Playwright/Puppeteer) to extract data
- Data probably accessible via JavaScript execution in browser context

### 4. Total Network Requests

**Total Requests:** 302
- 1 HTML document
- 2 JavaScript files
- 3 CSS files
- 179 character icon (WebP) files
- ~115 other assets (fonts, UI images, backgrounds)

## Character Sample by Edition

### Trouble Brewing (tb)
- chef_g, investigator_g, fortuneteller_g, ravenkeeper_g, drunk_g

### Bad Moon Rising (bmr)
- grandmother_g, gambler_g, lunatic_g, godfather_e, chambermaid_g

### Sects & Violets (snv)
- snakecharmer_g, dreamer_g, savant_g, philosopher_g, sweetheart_g

### Carousel
- balloonist_g, cannibal_g, amnesiac_g, widow_e, acrobat_g

### Fabled
- djinn, angel, buddhist, deusexfiasco, doomsayer

### Loric
- bootlegger, bigwig, gardener, stormcatcher, tor

## Scraping Strategy Recommendation

### ✓ RECOMMENDED: Browser Automation with DOM Extraction

**Why:**
1. No JSON API endpoint available
2. Character data embedded in JavaScript application
3. Icons publicly accessible via predictable URL pattern
4. Must render page to access character data

**Approach:**
1. Use **Playwright** (Python or Node.js)
2. Load script.bloodontheclocktower.com
3. Wait for page to fully render (character list populates)
4. Extract character data from DOM elements or JavaScript context
5. Download icons using discovered URL pattern

**Alternative Option:** JavaScript Context Extraction
- If character data is in a global JavaScript variable
- Use Playwright to execute: `page.evaluate(() => window.characterData)`
- May be faster than DOM scraping

## Next Steps

### Immediate Actions Needed

1. **Export Function Test**
   - User should try exporting all characters as JSON from the tool
   - This might give us the complete data structure
   - Would simplify scraping significantly

2. **DOM Inspection**
   - Inspect character list elements in browser DevTools
   - Document CSS selectors for character cards
   - Check for data attributes (data-id, data-character, etc.)

3. **JavaScript Console Test**
   - Open browser console on script.bloodontheclocktower.com
   - Try: `window`, `document.querySelector('#all-characters')`, etc.
   - Look for global variables containing character data

### Implementation Plan

Once we have the export JSON or DOM structure:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('https://script.bloodontheclocktower.com/')

    # Wait for characters to load
    page.wait_for_selector('#all-characters')

    # Option A: Extract from JavaScript context
    characters = page.evaluate('() => window.characterData')

    # Option B: Extract from DOM
    characters = page.query_selector_all('.character-card')

    # Extract character data
    # Download icons using URL pattern

    browser.close()
```

## Icon Download Strategy

Since we know the exact URL pattern, we can:

1. **Extract character IDs** from scraped data
2. **Determine edition** for each character
3. **Determine alignment** (good _g vs evil _e vs traveller/fabled)
4. **Construct icon URL** using pattern
5. **Download directly** (no need to scrape icons from page)

**Example:**
```python
def get_icon_url(character_id, edition, team):
    base = "https://script.bloodontheclocktower.com/src/assets/icons"

    # Determine suffix
    if team in ['townsfolk', 'outsider']:
        suffix = '_g'
    elif team in ['minion', 'demon']:
        suffix = '_e'
    else:  # traveller, fabled
        suffix = ''

    return f"{base}/{edition}/{character_id}{suffix}.webp"
```

## Outstanding Questions

1. ✓ Character icon format? → **WebP** (already optimized!)
2. ✓ Icon URL pattern? → **Documented above**
3. ✓ Total character count? → **175 characters**
4. ✓ Editions? → **tb, bmr, snv, carousel, fabled, loric**
5. ❓ Character data structure? → **Need export JSON or DOM inspection**
6. ❓ How to get ability text, reminders, night order? → **Need to test export or DOM scraping**

## Data We Still Need

From user investigation:

1. **Export JSON sample** - Export a few characters and share the JSON structure
2. **DOM structure** - CSS selectors for character elements
3. **JavaScript variables** - Any global vars containing character data
4. **Total character count** - How many characters when you select ALL?

