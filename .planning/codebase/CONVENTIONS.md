# Coding Conventions

**Analysis Date:** 2026-04-05

## Naming Patterns

**Files:**
- Simple lowercase names for runtime files (`app.py`, `manifest.json`, `sw.js`)
- Primary served frontend lives at `templates/index.html`
- Planning artifacts use uppercase markdown names (`PROJECT.md`, `REQUIREMENTS.md`)

**Functions:**
- Python functions use `snake_case`
- Route handlers are named after the action they perform (`list_torrents`, `save_position`, `download_file`)
- Helper functions are short and action-oriented (`ts_post`, `ts_get`, `set_viewed`)

**Variables:**
- Local Python variables use `snake_case`
- Configuration constants use `UPPER_SNAKE_CASE` (`TORRSERVER`, `JACRED_URL`, `POSITIONS_FILE`)
- Frontend JavaScript in the template follows `camelCase`

**Types:**
- No explicit type system is used in application code

## Code Style

**Formatting:**
- Python uses 4-space indentation
- String style is mostly double quotes in Python and JavaScript
- HTML/CSS/JS are co-located inline in the template instead of split by concern

**Linting:**
- No formatter or linter config is present
- No automated style enforcement is configured

## Import Organization

**Order:**
1. Python standard library imports
2. Third-party imports
3. Flask imports

**Grouping:**
- `app.py` uses grouped import blocks with blank-line separation

**Path Aliases:**
- None

## Error Handling

**Patterns:**
- Integration helpers catch broad exceptions and return `None`
- Search route falls back to empty results on failure
- Stream and download routes return `502` with a JSON payload on proxy failure

**Error Types:**
- No custom exception hierarchy
- Most failures are absorbed at the route/helper boundary instead of bubbling upward

## Logging

**Framework:**
- None in application code

**Patterns:**
- The code relies on process-level logging from Flask or the host environment

## Comments

**When to Comment:**
- Short section-divider comments are used in `app.py`
- Inline comments explain migrations, filtering rules, and sync heuristics

**JSDoc/TSDoc:**
- Not used

**TODO Comments:**
- No established in-code TODO convention detected

## Function Design

**Size:**
- Backend route handlers are medium-sized and often contain both orchestration and transformation logic
- Helpers are thin wrappers around remote HTTP calls or file persistence

**Parameters:**
- Route handlers mostly read from Flask `request`
- Helper functions use small explicit parameter lists

**Return Values:**
- JSON routes return Flask `jsonify(...)` payloads
- Helpers return `None` on failure rather than raising

## Module Design

**Exports:**
- The backend is a single module with Flask decorators rather than exported submodules
- Frontend code is embedded in one HTML template rather than split into modules

**Barrel Files:**
- Not applicable

---

*Convention analysis: 2026-04-05*
*Update when patterns change*
