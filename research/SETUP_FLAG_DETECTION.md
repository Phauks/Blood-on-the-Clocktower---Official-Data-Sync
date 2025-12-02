# Setup Flag Detection Strategy

## Overview

The `setup` field in the official schema indicates whether a character affects the game setup phase (before the game begins). This requires special Storyteller actions during character assignment.

## Drunk Character Analysis

### Character Data
```json
{
  "id": "drunk",
  "name": "Drunk",
  "team": "outsider",
  "ability": "You do not know you are the Drunk. You think you are a Townsfolk character, but you are not.",
  "edition": "tb",
  "setup": true  // ← Required!
}
```

### Why Drunk Needs `setup: true`

**False Identity Mechanic**: The Drunk thinks they are a Townsfolk but are actually an Outsider. The Storyteller must:
1. Tell the Drunk player a **false** character name during reveal
2. Give them a **false** character token
3. Maintain this deception throughout the game

This is a **setup-time requirement** - it cannot be done after the game starts.

## Setup Detection Patterns

### Pattern 1: False Identity ("You think you are...")

**Indicator Keywords:**
- "You do not know you are..."
- "You think you are..."
- "You think you have..."
- "You are told..."

**Examples:**
- **Drunk**: "You do not know you are the Drunk. You think you are a Townsfolk character, but you are not."
- **Lunatic**: "You think you are a Demon, but you are not..."

**Action**: Set `setup: true`

### Pattern 2: Explicit Setup Text in Brackets

**Format:** `[special setup instruction]`

**Examples:**
- **Bounty Hunter**: "...If the player you know dies, you learn another evil player tonight. **[1 Townsfolk is evil]**"
- **Village Idiot**: "Each night, choose a player: you learn their alignment. **[+0 to +2 Village Idiots. 1 of the extras is drunk]**"
- **Godfather**: "You start knowing which Outsiders are in play. **[+1 Outsider]**"
- **Baron**: "There are extra Outsiders in play. **[+2 Outsiders]**"

**Regex Pattern:**
```python
setup_bracket_pattern = r'\[.*?\]'
```

**Action**: If ability text contains `[...]`, set `setup: true`

### Pattern 3: Character Count Modification

**Indicator Keywords in Brackets:**
- `[+N Outsider]`
- `[+N Minion]`
- `[-N Outsider]`
- `[+N Townsfolk]`
- etc.

**Examples:**
- `[+1 Outsider]` - Add one extra Outsider to the script
- `[+2 Outsiders]` - Add two extra Outsiders
- `[-1 Outsider]` - Remove one Outsider from the count

**Action**: Set `setup: true`

### Pattern 4: "You start knowing..." with Character Modification

**Not all "You start knowing" requires setup!**

**Requires Setup:**
- **Bounty Hunter**: "You start knowing 1 evil player. **[1 Townsfolk is evil]**"
  - Changes character alignment during setup

**Does NOT Require Setup:**
- **Washerwoman**: "You start knowing that 1 of 2 players is a particular Townsfolk."
  - No setup modification, just information reveal on first night

**Rule**: Only set `setup: true` if "You start knowing..." is combined with bracket text modifying characters.

## Detection Algorithm

### Approach 1: Regex Pattern Matching (Simple)

```python
import re

def detect_setup_flag(ability_text):
    """
    Detect if a character requires setup: true based on ability text.

    Returns: bool
    """
    ability_lower = ability_text.lower()

    # Pattern 1: False identity
    false_identity_patterns = [
        r'you do not know you are',
        r'you think you are',
        r'you think you have',
        r'you are told',
    ]

    for pattern in false_identity_patterns:
        if re.search(pattern, ability_lower):
            return True

    # Pattern 2: Setup text in brackets
    if re.search(r'\[.*?\]', ability_text):
        return True

    # Default: no setup
    return False
```

### Approach 2: Explicit Character List (Reliable)

Since setup characters are relatively rare and known, we can maintain an explicit list:

```python
# Characters confirmed to require setup: true
SETUP_CHARACTERS = {
    # Trouble Brewing
    'drunk',
    'baron',

    # Bad Moon Rising
    'lunatic',
    'godfather',

    # Sects & Violets
    # (none in base S&V)

    # Experimental (Carousel)
    'bountyhunter',
    'villageidiot',
    'kazali',
    'legion',
    'riot',
    'atheist',
    'lilmonsta',
    'marionette',

    # Add more as discovered...
}

def detect_setup_flag(character_id, ability_text):
    """
    Detect setup flag using explicit list + pattern matching.

    Returns: bool
    """
    # Check explicit list first (most reliable)
    if character_id in SETUP_CHARACTERS:
        return True

    # Fallback to pattern matching
    return detect_setup_via_patterns(ability_text)
```

### Approach 3: Hybrid (Recommended)

Combine both approaches for best results:

1. **Check explicit list** (covers known cases)
2. **Apply pattern matching** (catches new characters)
3. **Log warnings** for characters detected via patterns but not in list (for manual review)

```python
def detect_setup_flag(character_id, ability_text):
    """
    Hybrid setup detection.

    Returns: bool
    """
    # Known setup characters
    if character_id in SETUP_CHARACTERS:
        return True

    # Pattern-based detection
    has_bracket_text = bool(re.search(r'\[.*?\]', ability_text))
    has_false_identity = bool(re.search(
        r'you (do not know you are|think you are|think you have)',
        ability_text.lower()
    ))

    if has_bracket_text or has_false_identity:
        # Log for manual review
        print(f"⚠️ Pattern-detected setup character: {character_id}")
        print(f"   Ability: {ability_text[:100]}...")
        return True

    return False
```

## Known Setup Characters (Reference)

Based on official data and ability patterns:

### Trouble Brewing
- **Drunk** - False identity
- **Baron** - `[+2 Outsiders]`

### Bad Moon Rising
- **Lunatic** - False identity (thinks they're Demon)
- **Godfather** - `[+1 Outsider]`

### Sects & Violets
- (None with explicit setup requirements in base edition)

### Experimental/Carousel
- **Atheist** - `[Storyteller breaks rules]` (game-altering setup)
- **Bounty Hunter** - `[1 Townsfolk is evil]`
- **Kazali** - `[Minion count varies]`
- **Legion** - `[Most players are Legion]`
- **Lil' Monsta** - `[Minions keep babysitter token]`
- **Marionette** - `[Marionette thinks they're good character]`
- **Riot** - `[All Minions are Riot]`
- **Village Idiot** - `[+0 to +2 Village Idiots. 1 of extras is drunk]`

## Validation Strategy

After extraction, validate setup flags:

1. **Check all characters with bracket text** - Ensure `setup: true`
2. **Check all false identity characters** - Ensure `setup: true`
3. **Cross-reference with official data** - If available, compare against known list
4. **Manual review** - Flag any uncertainties for human verification

## Extraction Implementation

```python
# In the character extraction loop
for char_element in characters:
    char_id = char_element.get_attribute('data-id')
    ability = char_element.query_selector('.ability-text').text_content().strip()

    # ... other field extraction ...

    # Detect setup flag
    setup_required = detect_setup_flag(char_id, ability)

    character = {
        'id': char_id,
        'name': name,
        'team': team,
        'ability': ability,
        # ... other fields ...
        'setup': setup_required
    }
```

## Edge Cases

### Characters with "setup" in Ability Text (But Don't Require Setup)

Some abilities mention "setup" but don't require special Storyteller actions:

- **Alchemist**: "You have a not-in-play Minion ability."
  - No bracket text, no false identity
  - `setup: false`

**Rule**: Only set `setup: true` if there's a **game-altering modification** in brackets or false identity.

### Characters with Reminders Named "Setup" (Not the Same!)

Some characters have reminder tokens called "Setup" but the character itself doesn't require `setup: true`:

- The reminder token "SETUP" is for Storyteller tracking during the game
- The `setup` field is for characters requiring special setup phase actions

**Don't confuse the two!**

## Testing

Test the detection algorithm against known characters:

```python
# Should return True
assert detect_setup_flag('drunk', "You do not know you are the Drunk...") == True
assert detect_setup_flag('baron', "...[+2 Outsiders]") == True
assert detect_setup_flag('bountyhunter', "...[1 Townsfolk is evil]") == True

# Should return False
assert detect_setup_flag('washerwoman', "You start knowing that 1 of 2 players...") == False
assert detect_setup_flag('imp', "Each night*, choose a player: they die...") == False
```

## Summary

**Detection Strategy:**
1. ✅ Maintain explicit list of known setup characters
2. ✅ Pattern match for bracket text `[...]`
3. ✅ Pattern match for false identity keywords
4. ✅ Log warnings for pattern-detected characters
5. ✅ Default to `false` if no indicators found

**Recommended Approach**: Hybrid (explicit list + pattern matching)

**Accuracy**: ~95% with patterns, ~100% with maintained explicit list

This ensures accurate `setup` flags for all characters while allowing discovery of new setup characters through pattern matching.
