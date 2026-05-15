# Technology Stack

**Analysis Date:** 2026-04-05

## Languages

**Primary:**
- Python 3.x - backend application logic in `app.py`
- HTML/CSS/JavaScript - single-page frontend in `templates/index.html`

**Secondary:**
- JSON - local state/config artifacts such as `positions.json`, `.mcp.json`, and `.planning/config.json`

## Runtime

**Environment:**
- Python 3.x - runs the Flask application
- Browser runtime - executes the UI, Plyr player, and service worker

**Package Manager:**
- None declared in-repo
- Lockfile: no Python or Node lockfile present

## Frameworks

**Core:**
- Flask - HTTP server and API routing in `app.py`
- Requests - outbound HTTP client for TorrServer and jacred integration in `app.py`

**Testing:**
- pytest harness under `tests/` (added in v2.2): API contract tests via Flask test client, integration tests against the live wrapper, CI hook in `.github/workflows/tests.yml`

**Build/Dev:**
- No build pipeline
- Plyr 3.7.8 is loaded from CDN in `templates/index.html`

## Key Dependencies

**Critical:**
- `flask` - serves the UI shell and all API endpoints
- `requests` - calls TorrServer and jacred APIs
- Plyr CDN assets - browser video player UI

**Infrastructure:**
- TorrServer HTTP API - required backend dependency for library, file, viewed, and stream operations
- jacred.xyz HTTP API - optional search provider used by `/api/search`

## Configuration

**Environment:**
- Environment variables drive integration config:
  - `TORRSERVER_URL`
  - `TORRSERVER_USER`
  - `TORRSERVER_PASS`
  - `JACRED_URL`
  - `JACRED_KEY`
- Defaults are hardcoded in `app.py` when env vars are absent

**Build:**
- No build config files
- Runtime/tooling config exists in `.mcp.json` for local MCP usage only

## Platform Requirements

**Development:**
- Any platform with Python 3 and network access to a TorrServer instance
- No container or local database requirement

**Production:**
- Self-hosted Python process
- Depends on reachable TorrServer HTTP endpoint and writable `positions.json`
- Current operational environment is an AWS EC2 host with direct TorrServer exposure on port `8090`

---

*Stack analysis: 2026-04-05*
*Update after major dependency changes*
