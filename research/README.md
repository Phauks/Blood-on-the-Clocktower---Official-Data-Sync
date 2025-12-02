# Research & Analysis Archive

This folder contains the investigative research documents from the initial project discovery phase. These documents are preserved for reference but are **no longer actively maintained**.

## Summary of Findings

**Conclusion**: All required character data can be extracted from the official script tool HTML at `https://script.bloodontheclocktower.com/`

## Document Index

| Document | Purpose |
|----------|---------|
| `COMPLETE_DATA_EXTRACTION.md` | **Master reference** - Final extraction plan with code examples |
| `SCRAPING_PLAN.md` | Initial investigation strategy |
| `HAR_ANALYSIS.md` | Network traffic analysis findings |
| `HTML_STRUCTURE_ANALYSIS.md` | DOM structure documentation |
| `EXPORT_ANALYSIS.md` | Script tool export function analysis |
| `JINX_EXTRACTION.md` | Jinx data extraction strategy |
| `SETUP_FLAG_DETECTION.md` | Setup flag detection patterns |
| `SPECIAL_FIELD_DETECTION.md` | Bag-duplicate special field detection |
| `FLAVOR_TEXT_RESEARCH.md` | Wiki flavor text availability research |
| `FLAVOR_TEXT_STRATEGY.md` | Incremental flavor text update strategy |

## Key Discoveries

### Data Sources
- **Character List**: `#all-characters .item[data-id]` - 174 characters
- **First Night Order**: `.first-night .item` - 125 characters
- **Other Night Order**: `.other-night .item` - 65 characters  
- **Jinxes**: `.jinxes-container .jinxes .item` - 131 jinx pairs
- **Icons**: Predictable URL pattern `https://script.bloodontheclocktower.com/src/assets/icons/{edition}/{id}{_suffix}.webp`

### Extractable Fields (~98% of schema)
✅ id, name, team, ability, edition, image, firstNight, otherNight, firstNightReminder, otherNightReminder, reminders, jinxes

### Fields Requiring Special Handling
- `setup` - Pattern matching on ability text (bracket notation `[...]`)
- `flavor` - Wiki scraping (only on character changes)
- `remindersGlobal` - Default to empty array (not extractable)
- `special` - Bag-duplicate detection via patterns

## Implementation Status

Research phase is **COMPLETE**. See `/src` for implementation.
