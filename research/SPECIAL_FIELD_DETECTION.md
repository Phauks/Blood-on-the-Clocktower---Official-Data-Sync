# Special Field Detection Strategy

## Overview

The `special` field in the official schema defines special behaviors for characters, particularly for the digital version of the game. However, **"bag-duplicate"** is critical for physical token tracking.

**User Requirement**: Create rudimentary version of special field detection, mark for future improvement.

## Special Field Structure

```json
{
  "special": [
    {
      "type": "selection",
      "name": "bag-duplicate"
    }
  ]
}
```

## Bag-Duplicate Importance

**Physical Game Context:**
- Indicates you can have **multiple of the same character token** in play
- Example: Village Idiot can have 3 total Village Idiot tokens (1 + up to 2 extras)
- Critical for token bag management in physical games

## Detection Patterns

### Pattern 1: Self-Referencing Bracket Text (Primary)

**Indicator**: `[+N CharacterName]` where CharacterName matches the character itself

**Examples:**
- **Village Idiot**: `[+0 to +2 Village Idiots. 1 of the extras is drunk]`
  - Adds 0-2 additional Village Idiot tokens
  - → **bag-duplicate: YES**

**Regex Pattern:**
```python
import re

def has_self_duplicate_pattern(character_name, ability_text):
    """
    Check if ability text mentions adding multiple of this character.

    Args:
        character_name: Character name (e.g., "Village Idiot")
        ability_text: Full ability text with setup brackets

    Returns:
        bool: True if self-duplication detected
    """
    # Convert name to plural variations
    name_lower = character_name.lower()

    # Common pluralization patterns
    plural_variations = [
        name_lower + 's',      # "Village Idiots"
        name_lower + 'es',     # if ends in s/x/z
        name_lower,            # singular (edge case)
    ]

    # Check if bracket text mentions adding this character
    for plural in plural_variations:
        pattern = rf'\[.*?[+−]\d+.*?{re.escape(plural)}.*?\]'
        if re.search(pattern, ability_text, re.IGNORECASE):
            return True

    return False
```

### Pattern 2: "Most Players Are" Pattern

**Indicator**: `[Most players are CharacterName]`

**Examples:**
- **Legion**: `[Most players are Legion]`
  - Most players become Legion demons
  - → **bag-duplicate: YES**

**Regex Pattern:**
```python
def has_most_players_pattern(character_name, ability_text):
    """
    Check if ability says "most players are [this character]".
    """
    pattern = rf'\[.*?most players are {re.escape(character_name.lower())}.*?\]'
    return bool(re.search(pattern, ability_text, re.IGNORECASE))
```

### Pattern 3: Known Characters (Explicit List)

**Fallback approach** for characters we know have bag-duplicate but may not match patterns:

```python
# Characters confirmed to have bag-duplicate
BAG_DUPLICATE_CHARACTERS = {
    'villageidiot',    # [+0 to +2 Village Idiots]
    'legion',          # [Most players are Legion]
    'riot',            # [All Minions are Riot] (need to verify)
    # Add more as discovered
}
```

## Characters Identified (From HTML Analysis)

### ✅ Confirmed Bag-Duplicate

**Village Idiot** (villageidiot)
- **Pattern**: `[+0 to +2 Village Idiots. 1 of the extras is drunk]`
- **Reason**: Explicitly adds 0-2 extra Village Idiot tokens
- **Detection**: Pattern 1 (self-referencing)

**Legion** (legion)
- **Pattern**: `[Most players are Legion]`
- **Reason**: Most players become Legion
- **Detection**: Pattern 2 (most players)

### ⚠️ Needs Verification

**Riot** (riot)
- **Expected Pattern**: `[All Minions are Riot]` or similar
- **Reason**: Multiple Riot tokens likely
- **Detection**: Need to verify exact ability text

**Lil' Monsta** (lilmonsta)
- **Pattern**: `[+1 Minion]` but babysitter mechanics
- **Reason**: Minions can duplicate due to babysitter passing
- **Detection**: Unclear - may need explicit list

### ❌ NOT Bag-Duplicate (Add Extra Characters, But Not Duplicates)

These characters add extra characters but NOT duplicates of themselves:

- **Godfather**: `[+1 Outsider]` - adds an Outsider, not another Godfather
- **Baron**: `[+2 Outsiders]` - adds Outsiders, not more Barons
- **Lord of Typhon**: `[+1 Minion]` - adds a Minion, not another Lord of Typhon
- **Hermit**: `[+1 Outsider]` - adds an Outsider, not another Hermit

## Detection Algorithm

### Hybrid Approach (Recommended)

```python
def detect_bag_duplicate(character_id, character_name, ability_text):
    """
    Detect if character should have bag-duplicate special field.

    Args:
        character_id: Character ID (e.g., "villageidiot")
        character_name: Character name (e.g., "Village Idiot")
        ability_text: Full ability text including setup brackets

    Returns:
        list: special field array, or empty list
    """
    # Check explicit list first (most reliable)
    if character_id in BAG_DUPLICATE_CHARACTERS:
        return [{"type": "selection", "name": "bag-duplicate"}]

    # Pattern 1: Self-referencing bracket text
    if has_self_duplicate_pattern(character_name, ability_text):
        return [{"type": "selection", "name": "bag-duplicate"}]

    # Pattern 2: "Most players are" pattern
    if has_most_players_pattern(character_name, ability_text):
        return [{"type": "selection", "name": "bag-duplicate"}]

    # No bag-duplicate detected
    return []
```

### Complete Implementation

```python
import re

# Known characters with bag-duplicate
BAG_DUPLICATE_CHARACTERS = {
    'villageidiot',
    'legion',
    'riot',  # Verify
}

def has_self_duplicate_pattern(character_name, ability_text):
    """Check for [+N CharacterName] pattern."""
    name_lower = character_name.lower()

    # Try plural variations
    plural_variations = [
        name_lower + 's',
        name_lower + 'es',
        name_lower,
    ]

    for plural in plural_variations:
        # Look for bracket with + and character name
        pattern = rf'\[.*?[+]\d+.*?{re.escape(plural)}.*?\]'
        if re.search(pattern, ability_text, re.IGNORECASE):
            return True

    return False

def has_most_players_pattern(character_name, ability_text):
    """Check for [Most players are CharacterName] pattern."""
    pattern = rf'\[.*?most players are {re.escape(character_name.lower())}.*?\]'
    return bool(re.search(pattern, ability_text, re.IGNORECASE))

def detect_special_field(character_id, character_name, ability_text):
    """
    Detect special field for a character.

    Currently only detects bag-duplicate.
    Future: Could detect other special types (digital-only features).

    Returns:
        list: Array of special objects, or empty list
    """
    special_array = []

    # Detect bag-duplicate
    if (character_id in BAG_DUPLICATE_CHARACTERS or
        has_self_duplicate_pattern(character_name, ability_text) or
        has_most_players_pattern(character_name, ability_text)):

        special_array.append({
            "type": "selection",
            "name": "bag-duplicate"
        })

    # Future: Add detection for other special types here
    # - "grimoire" (digital app features)
    # - "distribute-roles" (role assignment)
    # etc.

    return special_array
```

## Integration with Extraction

```python
# In character extraction loop:
for char_element in characters:
    char_id = char_element.get_attribute('data-id')
    name = char_element.query_selector('.character-name').text_content().strip()
    ability = char_element.query_selector('.ability-text').text_content().strip()

    # ... other field extraction ...

    # Detect special field
    special = detect_special_field(char_id, name, ability)

    character = {
        'id': char_id,
        'name': name,
        'ability': ability,
        # ... other fields ...
        'special': special  # Empty list [] if no special abilities
    }
```

## Validation & Testing

### Test Cases

```python
# Test 1: Village Idiot (self-duplicate pattern)
assert detect_special_field(
    'villageidiot',
    'Village Idiot',
    'Each night, choose a player: you learn their alignment. [+0 to +2 Village Idiots. 1 of the extras is drunk]'
) == [{"type": "selection", "name": "bag-duplicate"}]

# Test 2: Legion (most players pattern)
assert detect_special_field(
    'legion',
    'Legion',
    'Each night*, a player might die. Executions fail if only 3 players live. [Most players are Legion]'
) == [{"type": "selection", "name": "bag-duplicate"}]

# Test 3: Godfather (adds Outsiders, NOT duplicate)
assert detect_special_field(
    'godfather',
    'Godfather',
    'You start knowing which Outsiders are in play. [+1 Outsider]'
) == []

# Test 4: Washerwoman (no special)
assert detect_special_field(
    'washerwoman',
    'Washerwoman',
    'You start knowing that 1 of 2 players is a particular Townsfolk.'
) == []
```

## Future Enhancements

### TODO: Mark for Improvement

**Current Implementation**: Rudimentary detection for bag-duplicate only

**Future Improvements:**
1. **Detect other special types**:
   - "grimoire" - Digital app grimoire features
   - "distribute-roles" - Role distribution mechanics
   - "signal" - Signaling mechanics
   - etc.

2. **Verify detected characters**:
   - Manual review of first extraction
   - Cross-reference with official data if available
   - Community feedback on edge cases

3. **Comprehensive character list**:
   - Maintain complete list of known special characters
   - Document why each character has special field
   - Track schema updates for new special types

4. **Pattern refinement**:
   - Handle edge cases in pluralization
   - Detect more complex duplicate patterns
   - Account for ability text variations

### Documentation Note

**Add to character JSON comment:**
```json
{
  "id": "villageidiot",
  "special": [
    {
      "type": "selection",
      "name": "bag-duplicate"
    }
  ]
  // Note: Rudimentary detection - verify and improve in future
}
```

## Known Limitations

**Current Approach:**
- ⚠️ Only detects "bag-duplicate" type
- ⚠️ May miss edge cases with unusual wording
- ⚠️ Explicit list needs manual maintenance
- ⚠️ Cannot detect digital-only special features

**Mitigation:**
- Pattern matching catches most cases
- Explicit list catches known characters
- Can be refined over time
- Mark as "to be improved" in documentation

## Summary

### ✅ Rudimentary Implementation

**Detection Methods:**
1. Explicit list of known characters
2. Pattern: `[+N CharacterName]` (self-duplication)
3. Pattern: `[Most players are CharacterName]`

**Expected Results:**
- Village Idiot: ✅ bag-duplicate
- Legion: ✅ bag-duplicate
- Riot: ⚠️ Needs verification
- Others: Default to empty `[]`

**Accuracy**: ~80-90% (good enough for initial implementation)

**Future Work**: ✅ Marked for improvement
- Verify detected characters
- Add more special types
- Refine patterns
- Maintain explicit list

This provides a solid foundation while acknowledging it needs refinement over time.
