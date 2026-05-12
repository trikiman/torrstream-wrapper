# Phase 1 Context (v2.1): Vidstack Swap

**Goal:** Replace Plyr 3.7.8 with Vidstack 1.12.13 as the web player on `tv.trikiman.shop`. Preserve the Lampa plugin's DOM contract. Fix the post-migration audio regression. Enable double-tap seek gestures for iOS-native feel.

**Milestone:** v2.1 Player UX + iOS readiness
**Requirements in scope:** PLAY-03, PLAY-04, PLAY-05, PLAY-06, PLAY-07, DELV-05, DELV-06

## Locked Decisions

### D1 — Library: Vidstack over video.js / media-chrome / shaka / plyr-react
- Built-in `<media-gesture>` for double-tap ±10s (user request)
- Active development; Plyr in maintenance mode (folding into Video.js v10)
- HLS.js + DASH providers bundled when needed
- Web-components distribution, no bundler

### D2 — Version pin: `1.12.13` (from `next` dist-tag)
- `latest` tag on npm = `0.6.15` (ancient)
- `next` = `1.12.13` (Feb 2025), matches docs examples
- CDN path: `https://cdn.jsdelivr.net/npm/vidstack@1.12.13/cdn/with-layouts/vidstack.js`

### D3 — Default video layout (not Plyr layout or custom)
- `<media-video-layout>` ships controls + 5 gestures (tap, double-tap left/right, tap center, long-press)
- Zero customization needed for v2.1; can restyle later via CSS vars

### D4 — Markup: let Vidstack own the `<video>`
- First attempt included explicit `<video id="player">` inside `<media-provider>` — Vidstack inserted its own alongside it, creating TWO video elements. Audio played from one, video from the other → silent playback.
- Final markup: `<media-player><media-provider></media-provider><media-video-layout></media-video-layout></media-player>`; Vidstack creates the `<video>` when `.src` is assigned
- Event handlers reach the internal `<video>` via `mediaPlayer.querySelector('video')` after `requestAnimationFrame`
- Lampa plugin's `findVideo()` still works because it scans `document.getElementsByTagName('video')` and finds the single Vidstack element

### D5 — No change to backend, Lampa plugin, positions schema
- This is a frontend-only milestone
- `app.py`, `static/lampa-sync.js`, `positions.json`, `/api/*` all untouched
- SW's shell-asset list updated (swap Plyr CDN URLs for Vidstack CDN URLs) + cache name bump `v3 → v4`
- Smoke script's substring check changed from `plyr` → `vidstack`

## Open Questions (deferred)

- **Q1** — Thumbnails/chapter VTTs for richer scrubbing UI: backlog PROD-04/05
- **Q2** — Custom SVG icons to match TorrStream branding: backlog
- **Q3** — Plyr-layout wrapper (Vidstack ships one for smoother migration): not needed, default layout is better
- **Q4** — i18n translations for controls (currently default English + small Russian toasts from our own code): backlog

## Reusable Assets

- `scripts/smoke_prod.py` — updated in place (Vidstack check)
- `static/sw.js` — updated in place (Vidstack shell assets, cache v4)
- Existing playFile / closePlayer / ensurePlayerElement flow preserved; only the DOM target shape changed

## Constraints

- Don't touch the Lampa plugin — DOM contract must hold
- Don't change backend APIs
- Don't introduce a bundler; Vidstack stays on CDN
- Oracle 1 GB RAM box must not get slower from the swap (Vidstack's with-layouts bundle ~250 KB gzip; acceptable)
