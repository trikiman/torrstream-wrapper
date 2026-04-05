<!-- GSD:project-start source:PROJECT.md -->
## Project

**TorrStream**

TorrStream is a self-hosted web wrapper around TorrServer. It provides a single browser UI for browsing torrents, searching jacred, streaming or downloading files, and syncing watch progress across devices through server-side position state.

**Core Value:** A torrent added once should be easy to find, play, and resume from any device through one simple web UI.

### Constraints

- **Tech stack**: Keep the current Python Flask plus single-template frontend model unless a refactor is justified
- **Dependency**: TorrServer remains the source of torrent and stream data
- **Persistence**: Resume state currently lives in `positions.json`
- **Ops**: The repo and live deployment are not automatically synchronized
- **Quality**: No tests exist today, so refactors need explicit verification
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.x - backend application logic in `app.py`
- HTML/CSS/JavaScript - single-page frontend in `templates/index.html`
- JSON - local state/config artifacts such as `positions.json`, `.mcp.json`, and `.planning/config.json`
## Runtime
- Python 3.x - runs the Flask application
- Browser runtime - executes the UI, Plyr player, and service worker
- None declared in-repo
- Lockfile: no Python or Node lockfile present
## Frameworks
- Flask - HTTP server and API routing in `app.py`
- Requests - outbound HTTP client for TorrServer and jacred integration in `app.py`
- No automated test framework is configured in this repository
- No build pipeline
- Plyr 3.7.8 is loaded from CDN in `templates/index.html`
## Key Dependencies
- `flask` - serves the UI shell and all API endpoints
- `requests` - calls TorrServer and jacred APIs
- Plyr CDN assets - browser video player UI
- TorrServer HTTP API - required backend dependency for library, file, viewed, and stream operations
- jacred.xyz HTTP API - optional search provider used by `/api/search`
## Configuration
- Environment variables drive integration config:
- Defaults are hardcoded in `app.py` when env vars are absent
- No build config files
- Runtime/tooling config exists in `.mcp.json` for local MCP usage only
## Platform Requirements
- Any platform with Python 3 and network access to a TorrServer instance
- No container or local database requirement
- Self-hosted Python process
- Depends on reachable TorrServer HTTP endpoint and writable `positions.json`
- Current operational environment is an AWS EC2 host with direct TorrServer exposure on port `8090`
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- Simple lowercase names for runtime files (`app.py`, `manifest.json`, `sw.js`)
- Primary served frontend lives at `templates/index.html`
- Planning artifacts use uppercase markdown names (`PROJECT.md`, `REQUIREMENTS.md`)
- Python functions use `snake_case`
- Route handlers are named after the action they perform (`list_torrents`, `save_position`, `download_file`)
- Helper functions are short and action-oriented (`ts_post`, `ts_get`, `set_viewed`)
- Local Python variables use `snake_case`
- Configuration constants use `UPPER_SNAKE_CASE` (`TORRSERVER`, `JACRED_URL`, `POSITIONS_FILE`)
- Frontend JavaScript in the template follows `camelCase`
- No explicit type system is used in application code
## Code Style
- Python uses 4-space indentation
- String style is mostly double quotes in Python and JavaScript
- HTML/CSS/JS are co-located inline in the template instead of split by concern
- No formatter or linter config is present
- No automated style enforcement is configured
## Import Organization
- `app.py` uses grouped import blocks with blank-line separation
- None
## Error Handling
- Integration helpers catch broad exceptions and return `None`
- Search route falls back to empty results on failure
- Stream and download routes return `502` with a JSON payload on proxy failure
- No custom exception hierarchy
- Most failures are absorbed at the route/helper boundary instead of bubbling upward
## Logging
- None in application code
- The code relies on process-level logging from Flask or the host environment
## Comments
- Short section-divider comments are used in `app.py`
- Inline comments explain migrations, filtering rules, and sync heuristics
- Not used
- No established in-code TODO convention detected
## Function Design
- Backend route handlers are medium-sized and often contain both orchestration and transformation logic
- Helpers are thin wrappers around remote HTTP calls or file persistence
- Route handlers mostly read from Flask `request`
- Helper functions use small explicit parameter lists
- JSON routes return Flask `jsonify(...)` payloads
- Helpers return `None` on failure rather than raising
## Module Design
- The backend is a single module with Flask decorators rather than exported submodules
- Frontend code is embedded in one HTML template rather than split into modules
- Not applicable
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- One backend module, `app.py`, contains routing, integration logic, and local persistence
- One primary frontend template, `templates/index.html`, contains markup, styles, and client logic inline
- Server-side state is file-based, not database-backed
- External capability is delegated to TorrServer and jacred rather than implemented natively
## Layers
- Purpose: serve the HTML shell, manifest, and service worker
- Contains: `/`, `/manifest.json`, `/sw.js`
- Depends on: local files under `templates/` and `static/`
- Used by: browser clients
- Purpose: expose library, playback, search, and position endpoints
- Contains: `/api/*` route handlers in `app.py`
- Depends on: helper functions, file persistence, and external services
- Used by: the client-side app in `templates/index.html`
- Purpose: translate wrapper actions into TorrServer and jacred requests
- Contains: `ts_post()`, `ts_get()`, `get_viewed()`, `set_viewed()`, and `search()`
- Depends on: `requests` and environment configuration
- Used by: API route handlers
- Purpose: persist local playback state that TorrServer does not fully own
- Contains: `load_positions()` and `save_positions()`
- Depends on: local `positions.json`
- Used by: library, file-list, and playback position routes
## Data Flow
- Browser state lives in the single-page client
- Persistent wrapper state lives in `positions.json`
- Torrent catalog and file metadata live in TorrServer
## Key Abstractions
- Purpose: expose a friendlier app-specific API around TorrServer
- Examples: `/api/torrents`, `/api/add`, `/api/remove/<torrent_hash>`
- Pattern: thin Flask route over helper methods and JSON shaping
- Purpose: track resume state at the file level, not just the torrent level
- Examples: `positions.json` entries with `files`, `last_file_index`, and `updated`
- Pattern: file-backed dictionary keyed by torrent hash
- Purpose: keep the full UI in one delivered document
- Examples: `templates/index.html`
- Pattern: inline CSS + inline JavaScript in a monolithic template
## Entry Points
- Location: `app.py`
- Triggers: Flask process startup or `python app.py`
- Responsibilities: define routes, helpers, config defaults, and serve HTTP traffic
- Location: `templates/index.html`
- Triggers: browser load of `/`
- Responsibilities: render the UI, call backend APIs, and manage playback/search interactions
- Locations: `static/manifest.json`, `static/sw.js`
- Triggers: browser install/service-worker lifecycle
- Responsibilities: app metadata and shell asset caching
## Error Handling
- `ts_post()` and `ts_get()` swallow exceptions and return `None`
- Search failures return `{"Results": []}`
- Stream and download proxy failures return `502` JSON errors
## Cross-Cutting Concerns
- No explicit logging framework in app code
- Minimal request validation
- Most routes trust JSON/query input shape and depend on safe defaults
- No user authentication in the wrapper
- Optional service-to-service basic auth for TorrServer only
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
