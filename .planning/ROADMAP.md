# Roadmap: TorrStream

## Overview

Milestone v2.1 replaces the current Plyr-based player with Vidstack, restores audio playback, adds double-tap-to-seek, and verifies iOS Safari playback. The Lampa plugin must keep working without changes because it locates the underlying `<video>` element directly in the DOM. Work proceeds in two phases: swap the player with contract-preserving tests, then verify iOS and close out the smoke checklist.

Prior milestones (v1.0, v1.1, v2.0) are archived under `.planning/milestones/` (v2.0 archive pending final AWS termination).

## Active Milestone: v2.1 Player UX + iOS readiness

### Phases

- [x] **Phase 1: Vidstack Swap** — Replace Plyr in `templates/index.html` with Vidstack web components; preserve `<video>` discoverability for the Lampa plugin; fix audio regression; add double-tap gesture. (completed 2026-05-12)
- [x] **Phase 2: iOS Verification + Smoke Update** — Update smoke scripts for the new player markup, manual iOS/iPad test, close out remaining CUT-03 (AWS decommission). (completed 2026-05-12; AWS instance preserved per user, services stopped)

### Phase Details

#### Phase 1: Vidstack Swap

**Goal**: `tv.trikiman.shop` uses Vidstack as the video player. Users get audio on first play, double-tap ±10s seek, native-feeling iOS Safari touch UX. Lampa plugin continues working untouched.

**Depends on**: Nothing (v2.0 infrastructure is live; v2.1 is a frontend change)

**Requirements**: [PLAY-03, PLAY-04, PLAY-05, PLAY-06, PLAY-07, DELV-05, DELV-06]

**Success Criteria** (what must be TRUE):
1. Plyr CDN scripts removed from `templates/index.html`; Vidstack web components and CDN scripts added.
2. When user clicks Play, the `<video>` element starts with audio audible by default on desktop Chrome and Firefox.
3. On iOS Safari the player respects `playsinline` and does not force fullscreen; user can interact inline.
4. Double-tap left third rewinds 10s; right third fast-forwards 10s; center toggles play/pause.
5. `static/lampa-sync.js` — untouched — still finds the `<video>` element and round-trips position.
6. Service worker caches Vidstack's CDN assets (or gracefully tolerates them being uncacheable).
7. Production smoke against `tv.trikiman.shop` passes 9/9 with updated Vidstack marker check.

**Plans**: 3 plans

Plans:
- [ ] 01-01: Research the exact Vidstack CDN bundle, attribute API, and gesture component; pin versions.
- [ ] 01-02: Swap markup + scripts in `templates/index.html`; wire resume position + save-on-pause events into Vidstack event handlers.
- [ ] 01-03: Verify Lampa plugin round-trip against the new player markup (stub Lampa on TorrStream page as before).

#### Phase 2: iOS Verification + Smoke Update

**Goal**: Production is confirmed working on iOS Safari + iPad Safari. Smoke script updated. AWS instance can now be terminated.

**Depends on**: Phase 1

**Requirements**: [QUAL-02, QUAL-03, CUT-03]

**Success Criteria** (what must be TRUE):
1. `scripts/smoke_prod.py` no longer checks for Plyr; checks for Vidstack marker in shell; still passes 9/9.
2. Manual iOS walkthrough: Shell loads → library visible → tap torrent → tap playable file → player opens inline → audio plays → seek via slider and via double-tap → close and reopen → resumes from saved position.
3. `docs/SMOKE-TESTS.md` updated with the iOS walkthrough steps and the double-tap expectation.
4. AWS EC2 terminated, AWS webhook deleted from GitHub, `docs/DEPLOYMENT.md` updated to say Oracle is sole production.

**Plans**: 2 plans

Plans:
- [ ] 02-01: Update `scripts/smoke_prod.py` and `docs/SMOKE-TESTS.md` to reflect Vidstack; rerun production smoke.
- [ ] 02-02: AWS decommission (stop → snapshot → terminate); delete AWS webhook; update docs and archive v2.0 milestone.

## Progress

**Execution Order:** Phase 1 → Phase 2

| Phase | Plans Complete | Status |
|-------|----------------|--------|
| 1. Vidstack Swap | 3/3 | Complete | 2026-05-12 |
| 2. iOS Verification + Smoke Update | 2/2 | Complete | 2026-05-12 |

## Archived Milestones

### v2.0 Oracle Migration (shipped 2026-05-12, pending AWS terminate)
- 3 phases, 7 plans. Summary: deployment moved from AWS Frankfurt to Oracle Amsterdam; all user state preserved; domain + TLS + Lampa plugin URL unchanged; auto-deploy webhook working. See `.planning/phases/01-oracle-baseline/` for artifacts.

### v1.1 Cross-Client Position Sync (shipped 2026-04-29)
- 1 phase, 2 plans. See `.planning/milestones/v1.1-ROADMAP.md`.

### v1.0 TorrStream (shipped 2026-04-24)
- 4 phases, 11 plans. See `.planning/milestones/v1.0-ROADMAP.md`.
