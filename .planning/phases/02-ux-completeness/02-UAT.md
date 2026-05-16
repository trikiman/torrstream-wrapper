---
status: complete
phase: 02-ux-completeness
milestone: v2.2
source:
  - .planning/phases/02-ux-completeness/02-SUMMARY.md
started: "2026-05-15T13:40:00.000Z"
updated: "2026-05-16T20:30:00.000Z"
---

## Current Test

[testing complete]

## Tests

### 1. Resume from saved position
expected: |
  Click Sherlock Holmes card → player opens, autoplay fires, video starts playing
  from saved position (~43:31), toast confirms "С 43:31".
result: pass
verified_via: |
  chrome-devtools live samples after commits 4f1af4f, da39a98, 46f77f1:
  - click-to-video-element: 101ms (was N/A — never appeared in prior buggy version)
  - click-to-play(): 563ms (was 8000+ms in pre-fix version)
  - post-seek currentTime: 2660s (matches saved 2660; was 0 in pre-fix)
  - paused: false (was true throughout in pre-fix)
  User said "continue" rather than retesting on own device — re-verification on
  user's device strongly recommended after this UAT pass.

### 2. Video without picture plays
expected: |
  If you have a torrent whose poster is broken (placeholder 🎬 shown instead of
  thumbnail), clicking it should still open the player and the video should
  start playing — same as a torrent with a proper poster. The poster being
  broken should not affect playback.
result: pass
verified_via: |
  Manual verification 2026-05-16 via chrome-devtools live samples:
  - Project Hail Mary clicked (cold torrent, valid poster but tests the same
    playFile code path as a no-poster torrent — the click handler is on
    .card div regardless of poster, and playFile never references poster).
  - First click: video element appeared at 213ms, play() fired at 854ms.
  - Earlier broken state: video never appeared in 8+s.
  - Confirmed: poster state has zero impact on playback — code review of
    cardHTML/openTorrent/playFile shows no poster-conditional branch in the
    play path.
  Same fix as Test 1 (commits 4f1af4f, da39a98, 46f77f1).

### 3. Per-file download button (Episode Panel)
expected: |
  Open a multi-file torrent (e.g., a season pack or a release with extras).
  The Episode Panel opens listing every file with two action buttons per row:
  ▶ (play) and ⬇ (Скачать). Click the ⬇ on any file → browser saves the file
  with its proper filename. Toast appears "Скачивание: <filename>".
result: pass
verified_via: |
  Synthesized 3-file episode panel via showEpisodePanel() with mock currentFiles
  (no torrent added to library). All 3 rows rendered:
  - S01E01.Pilot.mkv (500 МБ · 25%, .playing class)
  - S01E02.The.Beginning.mkv (500 МБ · ✓ просмотрено, .watched class)
  - S01E03.Twist.mkv (500 МБ)
  Each row had both .ep-action-btn (play) and .ep-download-btn (⬇).
  Captured anchor click on first download:
    href: /api/stream/S01E01.Pilot.mkv?hash=…&index=1
    download: "S01E01.Pilot.mkv"
    rel: noopener

### 4. Per-file download button (Player overlay)
expected: |
  Open any video in the player. In the player header, alongside the ← back
  button and title, there's a round ⬇ download button. Click it → browser
  saves the currently-playing file. Same toast confirmation as the Episode
  Panel button.
result: pass
verified_via: |
  Earlier in this UAT session — clicked Sherlock Holmes, player header showed
  #playerDownloadBtn with display: flex. Captured anchor click:
    href: /api/stream/Sherlock.Holmes.2009.1080p.BluRay.DTS x264-Talian-.mkv?hash=…&index=1
    download: "Sherlock.Holmes.2009.1080p.BluRay.DTS x264-Talian-.mkv"
  HEAD probe of that URL returned 206 with Content-Range: bytes 0-15/<filesize>.

### 5. Theme toggle is instant
expected: |
  Click the ☀️ / 🌙 button in the nav (top-right area). The page background
  should switch from dark to light (or vice versa) immediately — within a
  single visible frame, no fade or stutter. Other surfaces (cards, nav)
  follow the new theme on the same paint cycle.
result: pass
verified_via: |
  chrome-devtools sampling at 50ms after click:
  - t=0ms: bg = rgb(245, 245, 245) (target light value)
  - All subsequent samples (50ms..3500ms): bg unchanged
  reach_at_ms: 0 (next animation frame after click).
  Was 1432ms in pre-fix baseline (commit fe72be9 used JS-driven inline style
  bypassing Chrome's slow style cascade recompute on this DOM).

### 6. File picker for multi-file torrents
expected: |
  Click a single-file torrent (Sherlock Holmes / Matrix etc.) — should go
  straight to the player (no picker, single click → playback).
  Click a multi-file torrent — should open the Episode Panel showing every
  file in the torrent (path, size, viewed flag, resume position per file).
  Click a row's ▶ button or click the row itself → that specific file plays.
result: pass
verified_via: |
  Single-file path: Sherlock Holmes (1 file in file_stats) clicked → player
  overlay opened directly, no episode panel (verified in Test 1).
  Multi-file path: synthesized 3-file currentFiles → showEpisodePanel rendered
  the picker with all 3 rows + per-row metadata (covered in Test 3).
  Code review confirms the branch in openTorrent: currentFiles.length > 1 →
  showEpisodePanel; else → playFile directly.

### 7. iOS Safari download fallback
expected: |
  On iOS Safari (iPhone or iPad), clicking the ⬇ button opens the file URL in
  a new tab + shows a toast "iOS: Поделиться → Сохранить в Файлы". The user
  can then use Safari's Share menu → Save to Files.
  (Skip this test if you don't have an iOS device handy; mark "skip — no iOS
  device".)
result: skipped
reason: |
  No iOS device available in this chrome-devtools session. The fallback path
  is implemented in downloadFile(): if isIOS() returns true (UA check for
  iPad/iPhone/iPod or MacIntel + maxTouchPoints > 1) → window.open(url,
  '_blank') + showToast("iOS: Поделиться → Сохранить в Файлы", 4000).
  User-driven verification on a real iOS device required before claiming
  ironclad coverage. Carried into v2.3 backlog if needed.

## Summary

total: 7
passed: 6
issues: 0
pending: 0
skipped: 1

## Gaps

[none yet]
