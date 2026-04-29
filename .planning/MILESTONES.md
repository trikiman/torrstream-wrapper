# Milestones

## v1.1 Cross-Client Position Sync (Shipped: 2026-04-29)

**Phases completed:** 1 phase, 2 plans, 5 tasks

**Key accomplishments:**

- Surfaced TorrServer-viewed torrents on the wrapper homepage with a `viewed_in_torrserver` flag so externally-watched media appears in `Продолжить просмотр` even when the wrapper has no local position.
- Added cross-origin support to `/api/position/*` so a Lampa-side plugin running on `https://lampa.mx` can read and write resume state directly against the wrapper.
- Shipped a self-contained Lampa plugin at `static/lampa-sync.js` that auto-seeks `<video>` to the wrapper-saved offset on player start and POSTs `{file_index, position, duration}` at a 5 s cadence plus on pause / destroy / pagehide / beforeunload.
- Hardened plugin lifecycle: lifecycle listeners register exactly once instead of accumulating under the Lampa-detection polling loop, and the resume seek bails when the user switches torrents during the wait-for-metadata window.
- End-to-end UAT confirms bidirectional sync: Lampa playback advances the wrapper position in real time, and re-opening the same torrent in Lampa restores the wrapper-saved offset.

---

## v1.0 TorrStream (Shipped: 2026-04-24)

**Phases completed:** 4 phases, 11 plans, 22 tasks

**Key accomplishments:**

- Added an authoritative runtime/deployment guide and removed ambiguity around the legacy root frontend file.
- Established a repeatable smoke-verification path and wired it into the project’s working instructions.
- Added structured library and file diagnostics so empty upstream state, failed file lookup, and playable-file absence are visible in both the API and the touch UI.
- Normalized add/remove mutation behavior so invalid input, upstream failures, and local cleanup outcomes are visible instead of implied.
- Expanded operational diagnostics and aligned the docs/state so maintainers can explain wrapper behavior without reading the code first.
- Added probe-driven playback/download diagnostics and visible player failure states for touch-first devices.
- Made resume-state persistence safer and turned completion writes into explicit sync-result responses.
- Connected playback completion UX to backend sync results so viewed-state updates are observable instead of implicit.
- Made search resilient under provider instability by surfacing outage state, retry behavior, and local-library fallback results in the UI.
- Turned installability into a visible product behavior with a real install button and Safari/iPad guidance instead of leaving it implicit in the manifest alone.
- Added a runnable smoke-check helper and aligned the docs/state so delivery verification is executable instead of purely manual.

---
