# Flavor Text Extraction Research

## Summary

**Status**: ✅ Flavor text IS available and extractable from wiki pages
**Difficulty**: ⚠️ **MODERATE** - Requires 174 additional HTTP requests
**Feasibility**: ✅ Achievable with acceptable complexity increase

## Findings

### Availability

Flavor text is **NOT** in the script tool HTML but **IS** available on individual character wiki pages at:
```
https://wiki.bloodontheclocktower.com/{CharacterName}
```

### Sample Flavor Texts Extracted

**Washerwoman**:
> "Bloodstains on a dinner jacket? No, this is cooking sherry. How careless."

**Drunk**:
> "I'm only a *hic* social drinker, my dear. Admittedly, I am a heavy *burp* socializer."

**Imp**:
> "We must keep our wits sharp and our sword sharper. Evil walks among us, and will stop at nothing to destroy us good, simple folk, bringing our fine town to ruin. Trust no-one. But, if you must trust someone, trust me."

### Location Pattern

**Consistent structure across all characters:**
1. Flavor text appears in the **Information box** section
2. Located **after** the character icon and metadata (Type, Artist)
3. **Before** the "Summary" heading
4. Presented as a standalone quote (often in character voice)

## Extraction Complexity Analysis

### Additional Work Required

**1. URL Construction** (Easy - 1 LOC)
```python
wiki_url = f"https://wiki.bloodontheclocktower.com/{character_name}"
```

**2. HTTP Requests** (Moderate - Network overhead)
- **174 characters** = **174 wiki page fetches**
- Estimated time: ~3-5 minutes total with rate limiting (1 request/second)
- Could parallelize with connection pooling (faster but more complex)

**3. HTML Parsing** (Moderate - Pattern matching)
```python
# Playwright/BeautifulSoup approach
# Find text in Information box, after metadata, before Summary
```

**4. Edge Cases** (Low complexity)
- Some characters might not have flavor text (handle gracefully)
- Special characters: `*hic*`, `*burp*` (asterisks for sound effects)
- Multi-line quotes (preserve formatting)
- HTML entities decoding (same as ability text)

### Difficulty Breakdown

| Task | Difficulty | Time Estimate |
|------|-----------|---------------|
| URL construction | Easy | 5 min |
| HTTP request logic | Easy | 15 min |
| HTML parsing | Moderate | 30-60 min |
| Edge case handling | Low | 15 min |
| Testing & validation | Moderate | 30 min |
| **TOTAL** | **Moderate** | **~2 hours** |

## Implementation Approach

### Option 1: Sequential Fetch (Simple, Slower)

**Pros:**
- Simple to implement
- Easy to debug
- Respectful of wiki server (rate limiting)

**Cons:**
- Slower (~3-5 minutes for all 174 characters)

**Code outline:**
```python
import time

for character in characters.values():
    wiki_url = f"https://wiki.bloodontheclocktower.com/{character['name']}"

    # Fetch page
    page = browser.new_page()
    page.goto(wiki_url)

    # Extract flavor text from Information box
    flavor = extract_flavor_text(page)
    character['flavor'] = flavor or ""  # Default to empty if not found

    page.close()
    time.sleep(1)  # Rate limiting - 1 request/second
```

### Option 2: Parallel Fetch (Complex, Faster)

**Pros:**
- Much faster (~30-60 seconds for all 174)

**Cons:**
- More complex (connection pooling, async)
- Higher server load (might get rate limited)

**Code outline:**
```python
import asyncio
from playwright.async_api import async_playwright

async def fetch_flavor(character):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"https://wiki.bloodontheclocktower.com/{character['name']}")
        flavor = await extract_flavor_text(page)
        await browser.close()
        return flavor

# Fetch 10 at a time (connection pooling)
flavors = await asyncio.gather(*[fetch_flavor(char) for char in characters.values()])
```

### Option 3: Hybrid (Recommended)

**Parallel batches with rate limiting:**
- Process 5-10 characters at a time
- 1-second delay between batches
- Balance between speed and server respect

**Estimated time**: ~1-2 minutes total

## Extraction Method

### HTML Structure (from wiki analysis)

The Information box contains:
```html
<div class="infobox">
  <img src="Icon_washerwoman.png">
  <div>Type: Townsfolk</div>
  <div>Artist: [Name]</div>
  <!-- FLAVOR TEXT HERE (no specific tag) -->
  <div>"Bloodstains on a dinner jacket? No, this is cooking sherry. How careless."</div>
</div>

<h2>Summary</h2>
```

### Extraction Strategy

**Pattern**: Text after metadata, before first `<h2>` heading

```python
def extract_flavor_text(page):
    """
    Extract flavor text from wiki Information box.

    Returns: str or None
    """
    # Try to find text in Information box
    infobox = page.query_selector('.infobox')
    if not infobox:
        return None

    # Get all text content
    text = infobox.text_content()

    # Pattern: Quote-like text between metadata and Summary
    # Usually starts with quotation mark or is in character voice
    # May need refinement based on actual HTML structure

    # Simple approach: Look for quoted text
    import re
    quote_match = re.search(r'"([^"]+)"', text)
    if quote_match:
        return quote_match.group(1)

    return None
```

## Impact on Overall Project

### Performance Impact

**Current scraping time** (without flavor):
- Character data: ~30 seconds
- Night order: ~10 seconds
- Jinxes: ~5 seconds
- **Total: ~45 seconds**

**With flavor text**:
- Additional time: **~2-3 minutes** (sequential) or **~1 minute** (parallel)
- **New total: ~3-4 minutes** (acceptable for daily automation)

### Code Complexity

**Current complexity**: Medium
**With flavor text**: Medium-High (+20% complexity)

**Why moderate increase?**
- Adds 1 new phase (wiki scraping)
- Adds error handling for 174 network requests
- Adds HTML parsing logic for a new source
- Increases testing surface area

### Maintenance Burden

**Risk**: Low to Medium

**Considerations:**
- Wiki HTML structure might change (would break flavor extraction)
- Could handle gracefully: if flavor fails, default to empty string
- Non-critical field - won't break character data if missing

### Data Quality

**Completeness**: ~99-100%
- Most characters have flavor text on wiki
- Some newer/experimental characters might not

**Accuracy**: High
- Direct from official wiki
- Manual review recommended for first extraction

## Recommendations

### Recommendation 1: Include Flavor Text ✅

**Reasoning:**
- Adds significant value for Token Generator (character cards look better with flavor)
- Difficulty is **moderate** but **manageable** (~2 hours implementation)
- Performance impact is **acceptable** (adds ~2 minutes to daily sync)
- Low risk (non-critical field, can fail gracefully)

### Recommendation 2: Implementation Strategy

**Suggested approach:**
1. **Start with Option 1** (sequential) for simplicity
2. **Add to Phase 7** of extraction (after jinxes, before icon downloads)
3. **Implement robust error handling**:
   - Log characters with missing flavor
   - Default to empty string if extraction fails
   - Continue processing even if wiki is down
4. **Add rate limiting** (1 request/second)
5. **Test with 5-10 characters first**
6. **Manual review** of first complete extraction

### Recommendation 3: Future Optimization (Optional)

If performance becomes an issue:
- Upgrade to Option 3 (parallel batches)
- Cache flavor text (rarely changes)
- Only re-fetch flavor when character is new/updated

## Code Integration

### Add to extraction phases:

**Phase 7: Flavor Text** (new phase, after jinxes)
```python
# Phase 7: Extract flavor text from wiki pages
print("Extracting flavor text from wiki...")

for char_id, character in characters.items():
    char_name = character['name']
    wiki_url = f"https://wiki.bloodontheclocktower.com/{char_name}"

    try:
        # Fetch wiki page
        wiki_page = browser.new_page()
        wiki_page.goto(wiki_url, timeout=10000)

        # Extract flavor text
        flavor = extract_flavor_text(wiki_page)
        character['flavor'] = flavor or ""

        wiki_page.close()

        # Rate limiting
        time.sleep(1)

        print(f"  ✓ {char_name}: {len(flavor) if flavor else 0} chars")
    except Exception as e:
        print(f"  ⚠ {char_name}: Failed to fetch flavor - {e}")
        character['flavor'] = ""  # Default to empty
```

## Summary

### ✅ **FEASIBLE**

**Difficulty**: Moderate
**Time to implement**: ~2 hours
**Performance impact**: +2-3 minutes per daily sync
**Risk**: Low (non-critical field)

### ✅ **RECOMMENDED**

Flavor text adds significant value to the project with acceptable complexity increase. The implementation is straightforward and can fail gracefully without breaking character data extraction.

### Decision

**Proceed with flavor text extraction**: YES / NO

If YES:
- Use Option 1 (sequential) for initial implementation
- Add comprehensive error handling
- Test thoroughly with sample characters
- Manual review of first full extraction

If NO:
- Document reason (complexity, time, or other priority)
- Mark as future enhancement
- Can add later without breaking existing data
