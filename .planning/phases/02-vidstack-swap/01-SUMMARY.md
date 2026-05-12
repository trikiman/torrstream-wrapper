---
phase: 02-vidstack-swap
milestone: v2.1
subsystem: frontend
tags: [vidstack, plyr, player, ios, gestures, sw]
provides:
  - Vidstack 1.12.13 as the production video player
  - Double-tap left/right seek ±10s, tap center play/pause
  - iOS Safari playsinline + inline player UX
  - Single <video> element (no duplicate) for correct audio playback
  - SW cache v4 with Vidstack shell assets
key-decisions:
  - "Let Vidstack own the <video>; event handlers attach post-rAF via mediaPlayer.querySelector('video')"
  - "Lampa plugin contract preserved (findVideo() still works)"
  - "Default video layout ships gestures out of the box; no custom gesture wiring needed"
requirements-completed: [PLAY-03, PLAY-04, PLAY-05, PLAY-06, PLAY-07, DELV-05, DELV-06]
duration: 90min
completed: 2026-05-12
commits:
  - f9d4c49 feat(player): swap Plyr -> Vidstack with default video layout
  - d58a316 fix(player): let Vidstack own the <video>; wire events to its internal element
---

# Phase 1 Summary: Vidstack Swap

**Outcome:** `tv.trikiman.shop` runs Vidstack 1.12.13 in production. Audio plays by default, double-tap seek is active, Lampa plugin round-trip still works, 9/9 smoke passes.

## Accomplishments

- Replaced Plyr 3.7.8 CDN links with Vidstack 1.12.13 (CSS theme, video-layout CSS, `with-layouts/vidstack.js` module)
- Wrapped the player in `<media-player><media-provider></media-provider><media-video-layout></media-video-layout></media-player>` (no explicit `<video>` child)
- Rewired `playFile()` to set `mediaPlayer.src` then locate Vidstack's internal `<video>` for event handlers
- Rewired `closePlayer()` to clear `mediaPlayer.src` instead of removing a direct `<video>`
- Service worker cache bumped to v4; shell asset list now references the three Vidstack CDN URLs instead of Plyr's
- Smoke script checks `vidstack` substring in shell (was `plyr`) and still passes 9/9
- CSS guard added: `media-player:not(:defined)` block prevents flash of unstyled content during web-component upgrade

## Validation (live on tv.trikiman.shop)

**E2E via Chrome DevTools MCP:**

| Check | Result |
|---|---|
| Single `<video>` element (no duplicate) | ✅ `video_count: 1` |
| Audio decoding | ✅ `webkitAudioDecodedByteCount > 0` |
| Video decoding | ✅ `webkitVideoDecodedByteCount > 0` |
| Default volume not muted | ✅ `muted: false, volume: 1.0` |
| Duration loaded | ✅ `duration: 634.6` (Big Buck Bunny) |
| Gesture elements rendered | ✅ `gesture_count: 5` |
| Double-tap ±10s seek | ✅ actions `["seek:-10", "seek:10"]` present |
| Play/pause toggle | ✅ `toggle:paused` gesture |
| Fullscreen gesture | ✅ `toggle:fullscreen` gesture |
| Controls toggle | ✅ `toggle:controls` gesture |
| Lampa plugin finds video | ✅ `videos_available: 1, first_has_finite_duration: true` |
| Plugin resume toast | ✅ "TorrStream: continued from 1:40" |
| Plugin seek to saved position | ✅ `currentTime: 100.00` (matched seeded 100) |
| Plugin position save | ✅ wrapper returned `position: 100` |

**Production smoke (scripts/smoke_prod.py):** 9/9 PASS

```
[PASS] Shell              200  440ms  bytes=53203   vidstack=True install_btn_ru=True
[PASS] Manifest           200  189ms  name='TorrStream' display='standalone' icons=1
[PASS] Service Worker     200  200ms  bytes=2337
[PASS] Lampa plugin       200  207ms  bytes=10046
[PASS] Status             200  194ms  ts.ok=True ts.count=3 wrapper.positions=5
[PASS] Library            200  199ms  items=3 state=ready
[PASS] Search             200 1028ms  results=841 ok=True
[PASS] Files[first]       200 4616ms  hash=7848e598e5b8
[PASS] CORS /api/position 204  192ms  allow-origin='*' methods='GET, POST, OPTIONS'
```

## Deviations from Plan

1. **Initial Vidstack bundle choice** — I first picked `latest` on npm (`0.6.15`). It was ancient. Switched to `next` dist-tag (`1.12.13`) after inspecting package metadata. Doc examples used the newer version.
2. **Double-video regression** — First pass kept the explicit `<video id="player">` inside `<media-provider>`. Vidstack inserted its own alongside. Two `<video>` elements → audio from one, video from the other. Root cause of the "silent playback" report. Fixed in commit `d58a316` by letting Vidstack own the element.
3. **No explicit gesture wiring needed** — Initial plan mentioned configuring gestures. Default layout ships them; nothing to do.

## Files Changed

| File | Change |
|---|---|
| `templates/index.html` | Plyr CDN → Vidstack CDN; wrap video in `<media-player>`; rewire playFile/closePlayer; CSS guards |
| `static/sw.js` | Cache name `v3 → v4`; shell asset list references Vidstack CDN URLs |
| `scripts/smoke_prod.py` | Shell body check now looks for `vidstack` instead of `plyr` |

## Issues Encountered

- Webhook auto-deploy had one transient `Recv failure: Connection reset` on `git push` — retry succeeded on the second try. Not a deploy bug.
- Console silently drops Plyr's autoplay-muted warnings (the original "no sound" source), which is why the issue wasn't caught before today's Oracle cutover; the fix resolves it for both AWS and Oracle going forward.

## Next Phase Readiness

Phase 2 — iOS Verification + AWS Decommission — ready to start. Open items:
- Update `docs/SMOKE-TESTS.md` with Vidstack-specific checks + iOS walkthrough
- Manual iOS Safari walkthrough on real device (user-driven)
- Terminate AWS EC2 (closes v2.0 CUT-03)
- Delete AWS GitHub webhook
- Update `docs/DEPLOYMENT.md` to reflect Oracle as sole production

---
*Phase 1 completed 2026-05-12 on tv.trikiman.shop. Commits `f9d4c49` and `d58a316`.*
