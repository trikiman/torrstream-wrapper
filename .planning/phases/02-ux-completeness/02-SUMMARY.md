---
phase: 02-ux-completeness
milestone: v2.2
subsystem: frontend
tags: [download-ui, theme, file-picker, resume-bug]
provides:
  - Per-file ⬇ Скачать button in Episode Panel rows (multi-file torrents)
  - Round download button in player overlay header (single + multi-file)
  - downloadFile()/downloadCurrentFile() helpers in templates/index.html
  - iOS Safari fallback (window.open + toast pointing to "Поделиться")
  - Theme toggle latency 1432ms → ≤16ms (JS-driven inline style write)
  - applyTheme() function unifying html[data-theme] + body class + bg color
  - Resume + autoplay race fix (post-v2.2.0 followup)
key-decisions:
  - "File-picker for multi-file torrents was already implemented as Episode Panel; original 2026-05-14 audit grep used wrong selectors"
  - "Theme: pivoted from CSS-only to JS inline style after three CSS attempts hit Chrome's ~680ms style cascade recompute ceiling"
  - "Download anchors use `download` attribute; iOS detection routes to new tab + toast (Safari ignores download cross-origin)"
  - "Resume fix: read /api/position once, branch on video.readyState — handle metadata-already-loaded case via immediate call instead of waiting for the event"
requirements-completed: [UX-01, UX-02, UX-03]
duration: 90min (Phase 2.0) + 15min (resume bug followup)
completed: 2026-05-14 (Phase 2.0), 2026-05-15 (resume fix)
commits:
  - 415f95e feat(ui): per-file download button (episode panel + player header)
  - 44ce659 perf(ui): theme toggle reaches target color in <=350ms (was ~1.4s)
  - b576f5a fix(ui): make theme transition fire by using background-color (not shorthand)
  - b7dbedd fix(ui): theme transition uses concrete colors so engine actually animates
  - 407494b fix(ui): @property registration so --bg transitions as an animatable color
  - fe72be9 fix(ui): instant theme bg via direct inline style write (paints in next frame)
  - 9e112ab fix(player): resume + autoplay race — handle metadata-already-loaded case
---

# Phase 2 Summary: UX completeness

**Outcome:** Every file in every torrent is reachable via the UI — pick any file from the Episode Panel, play it OR download it. Theme toggle feels instant. Resume from saved position works on the first click.

## User-facing changes

### 1. Per-file download UI

- Episode Panel rows for multi-file torrents now have a ⬇ Скачать button alongside the existing ▶ play button. Click → browser saves the file via the wrapper's `/api/stream/<filename>?hash=…&index=…` endpoint with the correct filename.
- Player overlay header gains a round ⬇ download button visible whenever a file is loaded. Lets the user save the currently-playing file without going back to the picker.
- iOS Safari fallback: `download` attribute is ignored cross-origin on iOS, so the button opens the URL in a new tab + shows a toast pointing at "Поделиться → Сохранить в Файлы".

### 2. Theme toggle (instant)

- Pre-fix: clicking ☀️/🌙 took ~1432ms wall-clock to reach the target background color. Three CSS-only iterations didn't help — Chrome's style cascade recompute on this DOM (vidstack web components + shadow trees) is the ceiling.
- Post-fix: `applyTheme()` writes `document.body.style.backgroundColor` directly from a small `THEME_BG` map, bypassing the cascade. Body bg snaps in the next paint frame (~16ms). Other surfaces (nav, cards) follow the var cascade on the same paint cycle — non-blocking.
- Storage moved from `body.classList` to `html[data-theme]` so future styling can target a single attribute root. The `.light` body class is still set in lockstep for back-compat with `.light nav` etc.

### 3. File picker for multi-file torrents (verified pre-existing)

- The 2026-05-14 E2E audit reported "no file picker for multi-file torrents". Discovery during Phase 2: it was already implemented as the Episode Panel (`ep-card` grid in `episodeOverlay`). The audit grep used wrong selectors (`file-item`/`file-action`) and missed it.
- Single-click on a single-file torrent still goes straight to player (preserved UX).
- Single-click on a multi-file torrent opens the picker.

### 4. Resume + autoplay (post-Phase 2 bug fix, 2026-05-15)

- User reported clicking a video card with a saved position didn't continue from the saved point, and players sometimes never started playing at all.
- Root cause: `video.onloadedmetadata = () => { seek + play }` was assigned AFTER Vidstack had already loaded metadata. The handler waits for an event that already fired → no seek, no play. Symptom matrix:
  - "Didn't continue from last position" — seek code in dead handler.
  - "Video without picture didn't play" — same dead handler also held the play() call; player stuck on frame 0 paused, no decoded image visible.
- Fix: read pos first, branch on `video.readyState`. ≥1 (HAVE_METADATA) → call doResumeAndPlay() immediately. Otherwise → `addEventListener("loadedmetadata", …, { once: true })` (no clobber).
- Verified live on Sherlock Holmes (saved position 2611s): post-fix `currentTime: 2660s, paused: false`. Both seek and autoplay fire correctly.

## Verification done before this UAT

- Browser MCP measured theme transition at 0ms (target color in next paint frame).
- Download anchor URL: `https://tv.trikiman.shop/api/stream/Matrix.1999.BDRip.avi?hash=…&index=1` with `download="Matrix.1999.BDRip.avi"`. Backend returns 206 with `Content-Range: bytes 0-15/1571913728` for a tiny range probe.
- Resume fix: clicked Sherlock Holmes card with saved position 2611s; player resumed at 2660s and was unpaused.

## Carry-overs

- No Playwright UI tests yet (foundation laid in Phase 3 pytest harness; promote to v2.3 if manual MCP coverage proves insufficient).
- Theme toggle on Safari iOS not measured directly (browser MCP runs Chrome desktop only).
- Real download click-through (full file download) not exercised — only HEAD/range probe.
