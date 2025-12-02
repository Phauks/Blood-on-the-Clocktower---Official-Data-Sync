# Flavor Text Extraction Strategy - INCREMENTAL UPDATES

## Decision

✅ **Include flavor text extraction with smart caching**

**Strategy**: Only fetch flavor text when necessary:
1. Flavor text is currently missing/empty
2. Character is new (doesn't exist in previous data)
3. Character has been updated (ability or other core fields changed)

## Benefits of Incremental Approach

### Performance

**First Run** (all 174 characters):
- Fetch all flavor texts: ~3-5 minutes
- One-time cost

**Daily Runs** (typical updates):
- Only 0-5 characters changed: ~5-30 seconds
- **99% faster** than re-fetching all flavor texts every day

### Server Load

**Respectful of wiki server:**
- First run: 174 requests (acceptable one-time operation)
- Daily runs: 0-5 requests typically
- Dramatically reduces wiki server load

### Reliability

**Graceful degradation:**
- If wiki is down, existing flavor texts remain intact
- Only new/updated characters would have missing flavor
- Can retry failed characters on next run

## Implementation Logic

### Detection Flow

```python
def needs_flavor_update(character, previous_character_data):
    """
    Determine if we need to fetch flavor text for this character.

    Args:
        character: Current character object (just scraped)
        previous_character_data: Character data from previous run (if exists)

    Returns:
        bool: True if flavor text fetch is needed
    """
    char_id = character['id']

    # Case 1: New character (not in previous data)
    if char_id not in previous_character_data:
        return True

    previous = previous_character_data[char_id]

    # Case 2: Flavor text is missing or empty
    if not character.get('flavor') or character.get('flavor') == "":
        return True

    # Case 3: Character has been updated (ability changed)
    if character['ability'] != previous.get('ability', ''):
        return True

    # Case 4: Character name changed (rare, but possible)
    if character['name'] != previous.get('name', ''):
        return True

    # Otherwise, keep existing flavor text
    return False
```

### Data Preservation

```python
def preserve_flavor_text(character, previous_character_data):
    """
    Copy flavor text from previous data if we're not updating it.

    Args:
        character: Current character object
        previous_character_data: Character data from previous run
    """
    char_id = character['id']

    if char_id in previous_character_data:
        previous_flavor = previous_character_data[char_id].get('flavor', '')
        if previous_flavor:
            character['flavor'] = previous_flavor
```

### Complete Extraction Phase

```python
# Phase 7: Flavor Text (incremental updates only)
print("Fetching flavor text (incremental updates)...")

# Load previous character data (from last successful run)
previous_data = load_previous_character_data()  # From data/characters/**/*.json

flavor_fetch_count = 0

for char_id, character in characters.items():
    # Check if we need to fetch flavor
    if needs_flavor_update(character, previous_data):
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

            flavor_fetch_count += 1
            print(f"  ✓ {char_name}: Fetched flavor ({len(flavor) if flavor else 0} chars)")

            # Rate limiting
            time.sleep(1)

        except Exception as e:
            print(f"  ⚠ {char_name}: Failed to fetch flavor - {e}")
            # Try to preserve previous flavor if available
            if char_id in previous_data:
                character['flavor'] = previous_data[char_id].get('flavor', '')
            else:
                character['flavor'] = ""
    else:
        # Preserve existing flavor text
        preserve_flavor_text(character, previous_data)

print(f"Flavor text: {flavor_fetch_count} fetched, {len(characters) - flavor_fetch_count} preserved")
```

## Previous Data Loading

### Load from Existing Character Files

```python
def load_previous_character_data():
    """
    Load all existing character JSON files from data/characters/*/*.json

    Returns:
        dict: {char_id: character_data}
    """
    import json
    from pathlib import Path

    previous_data = {}

    # Search all character files
    char_files = Path('data/characters').glob('**/*.json')

    for char_file in char_files:
        try:
            with open(char_file, 'r', encoding='utf-8') as f:
                character = json.load(f)
                char_id = character.get('id')
                if char_id:
                    previous_data[char_id] = character
        except Exception as e:
            print(f"Warning: Could not load {char_file}: {e}")

    return previous_data
```

### Alternative: Load from Manifest

```python
def load_previous_character_data_from_manifest():
    """
    Alternative: Load from manifest.json if it exists.

    Returns:
        dict: {char_id: character_data}
    """
    import json
    from pathlib import Path

    manifest_path = Path('data/manifest.json')

    if not manifest_path.exists():
        return {}

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    # If manifest includes full character data
    previous_data = {}
    for char_entry in manifest.get('characters', []):
        char_id = char_entry.get('id')
        if char_id:
            # Fetch individual character file
            edition = char_entry.get('edition')
            char_file = Path(f'data/characters/{edition}/{char_id}.json')
            if char_file.exists():
                with open(char_file, 'r', encoding='utf-8') as f:
                    previous_data[char_id] = json.load(f)

    return previous_data
```

## First Run Behavior

### Scenario: Empty Repository (Initial Sync)

**Behavior:**
- `previous_character_data` is empty `{}`
- All 174 characters trigger `needs_flavor_update() == True` (Case 1: New character)
- Fetches all 174 flavor texts
- Takes ~3-5 minutes

**Expected output:**
```
Fetching flavor text (incremental updates)...
  ✓ Washerwoman: Fetched flavor (72 chars)
  ✓ Librarian: Fetched flavor (58 chars)
  ✓ Investigator: Fetched flavor (64 chars)
  ... (171 more)
Flavor text: 174 fetched, 0 preserved
```

## Typical Daily Run Behavior

### Scenario: No Changes

**Behavior:**
- All characters exist in previous data
- No abilities changed
- All have flavor text already
- **0 flavor texts fetched** (all preserved)
- Takes ~1 second

**Expected output:**
```
Fetching flavor text (incremental updates)...
Flavor text: 0 fetched, 174 preserved
```

### Scenario: 1 New Character Added

**Behavior:**
- 173 characters preserved
- 1 new character fetched
- Takes ~2 seconds (1 request + 1 second rate limit)

**Expected output:**
```
Fetching flavor text (incremental updates)...
  ✓ NewCharacter: Fetched flavor (85 chars)
Flavor text: 1 fetched, 173 preserved
```

### Scenario: 3 Characters Updated

**Behavior:**
- 171 characters preserved
- 3 updated characters re-fetched
- Takes ~4 seconds (3 requests + 3 seconds rate limit)

**Expected output:**
```
Fetching flavor text (incremental updates)...
  ✓ UpdatedChar1: Fetched flavor (62 chars)
  ✓ UpdatedChar2: Fetched flavor (78 chars)
  ✓ UpdatedChar3: Fetched flavor (55 chars)
Flavor text: 3 fetched, 171 preserved
```

## Edge Cases

### Missing Flavor in Previous Data

**Scenario:** Character exists but has empty flavor `""`

**Behavior:**
- `needs_flavor_update()` returns `True` (Case 2)
- Fetches flavor text
- Updates character

**Use case:** Retry failed flavor fetches from previous run

### Wiki Down During Update

**Scenario:** Wiki is unreachable during daily sync

**Behavior:**
- Fetch fails with exception
- Preserves previous flavor text if available
- New characters get empty flavor `""`
- Next run will retry (Case 2: missing flavor)

**Code:**
```python
try:
    flavor = extract_flavor_text(wiki_page)
    character['flavor'] = flavor or ""
except Exception as e:
    print(f"  ⚠ {char_name}: Failed - {e}")
    # Preserve previous flavor if available
    if char_id in previous_data:
        character['flavor'] = previous_data[char_id].get('flavor', '')
        print(f"    → Preserved previous flavor")
    else:
        character['flavor'] = ""
        print(f"    → Will retry next run")
```

### Character Renamed

**Scenario:** Character name changes (rare)

**Behavior:**
- `needs_flavor_update()` returns `True` (Case 4)
- Fetches flavor text from new wiki URL
- Updates character

**Edge case:** Old wiki page might still exist with old flavor

## Manual Flavor Refresh

### Force Re-fetch All Flavor Texts

**Use case:** Wiki flavor texts were updated/improved

**Implementation:**
```python
# Add command-line flag: --refresh-flavor
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--refresh-flavor', action='store_true',
                   help='Force re-fetch all flavor texts')
args = parser.parse_args()

# In extraction phase:
if args.refresh_flavor:
    previous_data = {}  # Force all characters to be treated as new
    print("Force refreshing all flavor texts...")
```

**Usage:**
```bash
python scraper.py --refresh-flavor
```

## Performance Metrics

### Expected Performance

| Scenario | Characters Updated | Flavor Fetches | Time |
|----------|-------------------|----------------|------|
| First run | 174 (all new) | 174 | ~3-5 min |
| No changes | 0 | 0 | ~1 sec |
| 1 new character | 1 | 1 | ~2 sec |
| 5 characters updated | 5 | 5 | ~6 sec |
| 10 characters updated | 10 | 10 | ~11 sec |
| Force refresh | 174 (manual) | 174 | ~3-5 min |

### Daily Sync Impact

**Typical daily run** (0-2 characters changed):
- Previous: ~45 seconds (without flavor)
- With incremental flavor: ~47 seconds
- **Impact: +2 seconds** (negligible)

**Unusual day** (10 new characters):
- Previous: ~45 seconds
- With incremental flavor: ~56 seconds
- **Impact: +11 seconds** (acceptable)

## Testing Strategy

### Test Cases

1. **First run (empty repo)**
   - Verify all 174 characters fetch flavor
   - Verify all flavors are non-empty (or log missing ones)

2. **Second run (no changes)**
   - Verify 0 flavors fetched
   - Verify all 174 flavors preserved

3. **Add 1 new character**
   - Verify only new character fetches flavor
   - Verify 173 preserved

4. **Update 1 character ability**
   - Verify only updated character fetches flavor
   - Verify 173 preserved

5. **Wiki failure**
   - Mock wiki down
   - Verify previous flavors preserved
   - Verify new characters get empty flavor

6. **Force refresh**
   - Verify all 174 re-fetched
   - Verify updated flavors saved

## Summary

### ✅ Incremental Strategy Benefits

1. **Performance**: 99% faster on daily runs (0-5 seconds vs 3-5 minutes)
2. **Server-friendly**: Only 0-5 requests per day typically
3. **Reliable**: Preserves existing data on failures
4. **Flexible**: Can force refresh when needed
5. **Efficient**: Only fetches what's necessary

### Implementation Checklist

- [ ] Implement `load_previous_character_data()`
- [ ] Implement `needs_flavor_update()`
- [ ] Implement `preserve_flavor_text()`
- [ ] Add Phase 7 with incremental logic
- [ ] Add `--refresh-flavor` CLI flag
- [ ] Add comprehensive error handling
- [ ] Test all 6 test cases
- [ ] Document in changelog when flavor is fetched

### Decision Confirmed

**Include flavor text extraction with incremental updates** ✅

This approach provides the best balance of completeness, performance, and maintainability.
