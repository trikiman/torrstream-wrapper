# Codebase Structure

**Analysis Date:** 2026-04-05

## Directory Layout

```text
torrserver/
├── .codex/                # GSD skills, workflows, templates, and local agent tooling
├── .planning/             # GSD planning artifacts for this brownfield repo
├── docs/                  # Legacy docs directory
├── static/                # PWA assets: manifest, service worker, icons
├── templates/             # Served HTML frontend templates
├── .mcp.json              # Local MCP server config for tooling
├── app.py                 # Flask backend and integration logic
├── CLAUDE.md              # Generic legacy Claude Flow instructions
├── index.html             # Legacy root HTML prototype, not served by Flask
├── positions.json         # File-backed playback state
├── repomix-output.xml     # Generated repo snapshot artifact
├── vectors.db             # Local generated database artifact
├── key.pem                # Local key material artifact
└── second key.pem         # Local key material artifact
```

## Directory Purposes

**`.codex/`**
- Purpose: local GSD workflow framework and project skills
- Contains: agent definitions, workflows, templates, skill entrypoints
- Key files: `.codex/skills/gsd-new-project/SKILL.md`, `.codex/get-shit-done/workflows/new-project.md`
- Subdirectories: `agents/`, `get-shit-done/`, `skills/`

**`.planning/`**
- Purpose: project planning artifacts created by GSD
- Contains: config, project state, roadmap, requirements, codebase map
- Key files: `.planning/config.json`, `.planning/PROJECT.md`, `.planning/ROADMAP.md`
- Subdirectories: `codebase/`

**`static/`**
- Purpose: non-template frontend assets
- Contains: `manifest.json`, `sw.js`, `icons/icon-512.png`
- Key files: `static/manifest.json`, `static/sw.js`

**`templates/`**
- Purpose: server-served HTML documents
- Contains: `index.html`
- Key files: `templates/index.html`

**`docs/`**
- Purpose: legacy documentation area
- Contains: no active project markdown after stale doc removal

## Key File Locations

**Entry Points:**
- `app.py`: backend startup and all Flask routes
- `templates/index.html`: main client UI
- `static/sw.js`: service-worker entry

**Configuration:**
- `.planning/config.json`: GSD workflow preferences
- `.mcp.json`: local MCP tool configuration
- `app.py`: runtime env-var defaults for TorrServer and jacred

**Core Logic:**
- `app.py`: all backend logic
- `templates/index.html`: all frontend rendering, state, and API calls
- `positions.json`: persisted sync state

**Testing:**
- No test directory or test files currently exist

**Documentation:**
- `AGENTS.md`: Codex-facing project instructions generated from planning docs
- `CLAUDE.md`: legacy generic agent config, not authoritative for project behavior
- `.planning/`: primary planning and project memory documents

## Naming Conventions

**Files:**
- Python module: `app.py`
- Static assets use simple lowercase names (`manifest.json`, `sw.js`)
- Planning docs use uppercase names for top-level artifacts (`PROJECT.md`, `ROADMAP.md`)

**Directories:**
- Lowercase directory names for app/runtime folders (`static`, `templates`, `docs`)
- Hidden dot-directories for tooling and planning (`.codex`, `.planning`)

**Special Patterns:**
- GSD codebase docs live under `.planning/codebase/`
- GSD skills always expose a `SKILL.md`

## Where to Add New Code

**New Backend Feature:**
- Primary code: `app.py` unless the repo is first refactored into modules
- Tests: create a new `tests/` tree
- Config if needed: env vars referenced from `app.py`

**New Frontend Feature:**
- Implementation: `templates/index.html`
- Static supporting assets: `static/`
- Tests: create a new `tests/` or browser-test directory

**New Documentation/Planning:**
- Project planning: `.planning/`
- Tooling/workflow docs: `.codex/`
- Avoid adding new ad hoc root markdown files for project state

## Special Directories

**`.codex/`**
- Purpose: installed workflow framework and local skills
- Source: generated/managed by local tooling
- Committed: yes, currently present in repo

**`.planning/`**
- Purpose: live planning state for the project
- Source: generated and updated through GSD workflows
- Committed: intended to be tracked (`commit_docs: true`)

**Generated artifacts in root**
- `repomix-output.xml`, `vectors.db`, and local key files are collateral artifacts, not application source
- Changes here should be treated carefully and usually kept out of product work

---

*Structure analysis: 2026-04-05*
*Update when directory structure changes*
