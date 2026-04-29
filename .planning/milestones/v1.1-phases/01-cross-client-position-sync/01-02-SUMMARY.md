---
phase: 01-cross-client-position-sync
plan: 02
subsystem: plugin
tags: [lampa, plugin, lifecycle, devin-review]
requires:
  - phase: v1.1/01-01
    provides: lampa-sync plugin v1
provides:
  - deduplicated lifecycle listeners
  - torrent-switch-safe resume seek
affects: [plugin]
tech-stack:
  added: []
  patterns:
    - module-init listener registration with named handlers
    - resume-seek polling with current-state guards
key-files:
  created: []
  modified:
    - static/lampa-sync.js
key-decisions:
  - "Lifecycle listener registration belongs at module init, never inside a poll loop, even if the loop is bounded."
  - "tryResume's seek-when-ready loop must validate that the user is still on the torrent it was started for before applying the seek."
patterns-established:
  - "Name event handlers so the browser can deduplicate them; never register fresh anonymous functions in a loop."
requirements-completed: [QUAL-02]
duration: 25min
completed: 2026-04-29
pr: 4
commit: 5cddb48
---

# Phase 1 Plan 02: Lampa plugin lifecycle hardening

**Deduplicated plugin lifecycle listeners and made the resume seek safe under torrent switches.**

## Performance

- **Duration:** ~25 min (review, fix, push, merge, deploy verification)
- **Started:** 2026-04-29T07:30:00+00:00
- **Completed:** 2026-04-29T08:00:00+00:00 (PR #4 merged)
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Moved `beforeunload`, `pagehide`, and `visibilitychange` registration into `registerLifecycleListeners()` and extracted the visibilitychange callback to a named `onVisibilityChange`. Listeners now register exactly once instead of up to 60 times.
- `tryResume()`'s seek-when-ready interval now checks `current.hash`/`current.file_index` on each tick and bails if the user has navigated away.
- Live verification on `https://tv.trikiman.shop/static/lampa-sync.js` after auto-deploy confirms the new helpers shipped.

## Task Commits

1. **Task 1: Register lifecycle listeners exactly once** — PR #4 merge `5cddb48`
2. **Task 2: Bail resume seek on torrent switch** — PR #4 merge `5cddb48`

## Files Created/Modified
- `static/lampa-sync.js` — `registerLifecycleListeners()` extracted; `onVisibilityChange` named; `tryResume()` seek interval gains current-state guard.

## Decisions Made
- The previous registration ran inside `attemptInit()`, which could be called up to 60 times by the Lampa-detection polling loop. The browser deduplicates same-reference handlers but not freshly-allocated anonymous ones, so the visibilitychange handler could accumulate up to 60 copies. Fixing this is non-negotiable for tab-switch behavior.
- The seek-when-ready interval previously had no concept of "still on the right torrent", so a fast user who started torrent A then switched to torrent B before metadata loaded could end up with B seeked to A's saved position. Cheap fix, real correctness benefit.

## Deviations from Plan

None.

## Issues Encountered

- None during the fix itself; merge ran cleanly via direct GitHub REST after the same `git-manager` proxy 403 was bypassed with the `GIT_CONFIG_NOSYSTEM=1` workaround established in plan 01-01.

## User Setup Required

None. The plugin URL is unchanged and the auto-deploy webhook picks up the fix.

## Next Phase Readiness

v1.1 is feature-complete pending end-to-end UAT in `01-UAT.md`. No follow-up phase is currently planned.

---
*Phase: 01-cross-client-position-sync*
*Completed: 2026-04-29*
*PR: https://github.com/trikiman/torrstream-wrapper/pull/4*
