# TorrStream

## What This Is

TorrStream is a self-hosted web wrapper around TorrServer. It provides a single browser UI for browsing torrents, searching jacred, streaming or downloading files, and syncing watch progress across devices through server-side position state.

## Core Value

A torrent added once should be easy to find, play, and resume from any device through one simple web UI.

## Requirements

### Validated

- ✓ Browse the TorrServer library and inspect playable files
- ✓ Add and remove torrents through the wrapper API
- ✓ Stream and download media through the wrapper with resume support
- ✓ Persist per-file watch state and sync viewed markers back to TorrServer
- ✓ Search jacred and add results to TorrServer

### Active

- [ ] Establish brownfield planning artifacts and a codebase map for future GSD-driven work
- [ ] Align repo documentation and instructions with the current runtime and deployment reality
- [ ] Add a repeatable verification path for library, playback, sync, and search flows

### Out of Scope

- Replacing TorrServer as the media engine
- Multi-user accounts and social features
- Native mobile or TV apps

## Context

- The backend is a compact Flask app in `app.py`.
- The frontend is primarily a single monolithic template in `templates/index.html`.
- Persistent resume state is stored in local `positions.json`.
- The repo contains a legacy duplicate root `index.html`.
- Current live infrastructure has direct TorrServer access on EC2, while this wrapper repo remains a separate application codebase.
- No automated test suite or dependency manifest is present yet.

## Constraints

- **Tech stack**: Keep the current Python Flask plus single-template frontend model unless a refactor is justified
- **Dependency**: TorrServer remains the source of torrent and stream data
- **Persistence**: Resume state currently lives in `positions.json`
- **Ops**: The repo and live deployment are not automatically synchronized
- **Quality**: No tests exist today, so refactors need explicit verification

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep a wrapper architecture over TorrServer | Streaming and torrent-state logic already exist upstream | ✓ Good |
| Store playback progress in `positions.json` | Simple persistence for a personal deployment | ⚠️ Revisit |
| Use a single HTML template for the UI | Fast iteration with minimal tooling | ⚠️ Revisit |
| Start brownfield work by generating `.planning/` artifacts | The repo has code but no structured planning state | ✓ Good |

---
*Last updated: 2026-04-05 after brownfield GSD initialization*
