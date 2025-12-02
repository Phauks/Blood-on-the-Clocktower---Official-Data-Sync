# Scraping Investigation Plan

## Objective
Extract official character data and icons from **script.bloodontheclocktower.com** (The Pandemonium Institute's official script tool)

## Investigation Strategy

### Phase 1: Browser DevTools Investigation (Manual)

Before implementing the scraper, we need to manually investigate the website using browser DevTools to understand:

#### 1. Network Tab Analysis
- **Open script.bloodontheclocktower.com in Chrome/Firefox**
- **Open DevTools → Network tab**
- **Refresh the page and observe all network requests**

Look for:
- [ ] Any JSON files being fetched (characters.json, roles.json, data.json, etc.)
- [ ] API endpoints being called
- [ ] JavaScript bundle files (app.js, main.js, vendor.js)
- [ ] Character icon URLs (SVG files)
- [ ] Base URL patterns for images

**Document:**
- All JSON endpoint URLs
- Character image URL patterns
- How data is loaded (on page load, lazy loaded, etc.)

#### 2. DOM Structure Analysis
- **Open DevTools → Elements tab**
- **Find a character in the character list**

Look for:
- [ ] HTML structure of character cards/items
- [ ] CSS classes used for characters
- [ ] Data attributes (data-id, data-character-id, etc.)
- [ ] How character icons are embedded (img src, inline SVG, background-image)
- [ ] Container elements for character lists

**Document:**
- CSS selectors for character elements
- How to identify character team/category
- How to extract character IDs

#### 3. JavaScript Analysis
- **Open DevTools → Sources tab**
- **Find the main JavaScript bundle**

Look for:
- [ ] Global variables containing character data (window.characters, app.roles, etc.)
- [ ] Vue/React component data structures
- [ ] Character data embedded in JavaScript
- [ ] How images are referenced

**Document:**
- JavaScript variable names containing character data
- Data structure format
- How to access the data

#### 4. Console Exploration
- **Open DevTools → Console tab**
- **Try accessing potential data variables:**

```javascript
// Try these commands in the console:
console.log(window);  // Look for character data
console.log(document.querySelector('[data-character]'));  // Find character elements
console.log(localStorage);  // Check for cached data
console.log(sessionStorage);  // Check for session data

// Try to find Vue/React app instance
console.log(document.querySelector('#app').__vue__);  // If Vue
console.log(document.querySelector('#root')._reactRootContainer);  // If React
```

**Document:**
- How to access character data programmatically
- App framework being used (Vue, React, vanilla JS)

### Phase 2: Export Function Investigation

The script tool has an export feature - investigate this:

#### 1. Export Test
- **Create a script with a few characters**
- **Export as JSON**
- **Examine the exported JSON structure**

Look for:
- [ ] Does it include full character data or just IDs?
- [ ] Are image URLs included?
- [ ] What fields are present?

**Document:**
- Export JSON structure
- Whether this gives us full character data

#### 2. Maximum Export
- **Select ALL characters from all teams**
- **Export as JSON**
- **Count total characters**

This will tell us:
- [ ] Total number of official characters
- [ ] Whether we can get all data via export
- [ ] If images are included

### Phase 3: Image Source Investigation

#### 1. Icon URL Patterns
- **Find character icons on the page**
- **Right-click → Open Image in New Tab**

Document:
- [ ] Base URL for images
- [ ] URL pattern (e.g., `/icons/{id}.svg`, `/assets/characters/{team}/{id}.png`)
- [ ] Image format (SVG, PNG, WebP)
- [ ] Resolution/size

#### 2. SVG Source
- **View SVG source code**
- **Check if SVG is inline or external file**

Document:
- [ ] Whether SVGs are inline or external files
- [ ] SVG dimensions
- [ ] If they contain embedded raster images

### Phase 4: Scraping Strategy Decision

Based on findings above, choose approach:

**Option A: JSON Endpoint Scraping**
- If character data is available via JSON endpoint
- Fast and reliable
- Minimal processing needed

**Option B: Export Function Automation**
- If export function provides all data
- Use Playwright to trigger export
- Parse exported JSON

**Option C: DOM Scraping**
- If data is only in rendered DOM
- Use Playwright to render page
- Extract from HTML elements
- Most complex, but works if no API exists

**Option D: JavaScript Variable Extraction**
- If data is in global JavaScript variables
- Use Playwright to execute JS and extract data
- Moderate complexity

### Expected Deliverables

After manual investigation, document:

1. **Character Data Source:**
   - Exact URL or method to get character data
   - Data format and structure
   - Total character count

2. **Image URLs:**
   - URL pattern for character icons
   - Image format
   - Whether they're publicly accessible

3. **Scraping Approach:**
   - Recommended method (A, B, C, or D above)
   - Required tools (Playwright vs. simple HTTP requests)
   - Estimated complexity

4. **Sample Data:**
   - Export sample JSON from the tool
   - Screenshot of DevTools Network tab
   - List of 5-10 character icon URLs

## Next Steps

Once investigation is complete:
1. Update CLAUDE.md with findings
2. Choose technology stack (Python + Playwright vs. Node + Puppeteer)
3. Implement proof-of-concept scraper for 10 characters
4. Validate data against official schema
5. Implement full scraper

---

## Investigation Checklist

- [ ] Network tab analyzed - JSON endpoints identified
- [ ] DOM structure documented - CSS selectors noted
- [ ] JavaScript analyzed - data variables found
- [ ] Console exploration complete
- [ ] Export function tested
- [ ] All characters exported and counted
- [ ] Image URLs documented
- [ ] Scraping strategy chosen
- [ ] Sample data collected
- [ ] Findings documented in CLAUDE.md
