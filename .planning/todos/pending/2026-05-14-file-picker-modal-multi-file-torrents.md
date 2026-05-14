---
created: 2026-05-14T23:24:58.665Z
title: File-picker modal for multi-file torrents
area: ui
files:
  - templates/index.html
  - app.py:322
---

## Problem

Clicking a torrent card in TorrStream opens the player overlay directly, even
for multi-file torrents (TV packs, remuxes with extras, season releases). The
template auto-picks one file (presumably the largest playable) and goes
straight to play. There is no UI affordance to:

- See the full file list inside a torrent
- Pick a non-default file (episode 3 of a season pack, alternate audio, etc.)
- See per-file viewed status / position / size

Backend already returns this data: `GET /api/files/<hash>` returns
`file_stats: [{id, length, path, position, viewed, file_duration}, ...]` with
`has_playable_files`, `playable_count`, etc.

Confirmed during E2E audit 2026-05-14: `grep "file-action|file-play|file-item"
templates/index.html` → 0 matches. The DOM hook does not exist.

This becomes a real UX gap as soon as the user adds anything other than a
single-movie torrent. Lampa already exposes a file picker, so today users have
to use Lampa for multi-file content.

## Solution

Robust:

1. Design a file-picker modal that opens BEFORE the player when
   `file_stats.length > 1`, with single-file torrents preserving the current
   single-click straight-to-play UX.
2. Modal shows: file path (or basename), size, duration if known, viewed flag,
   resume position. Click → loads that index into the player.
3. Wire the file-picker into the same auto-warmup path the backend already
   does on cold torrents (so opening a multi-file torrent that's `Torrent in db`
   triggers warmup once and then renders files).
4. Pair with the download UI todo — same modal can host both Play and Скачать
   per file.
5. Add a SMOKE-TESTS.md step: pick a known multi-file torrent (e.g., a season
   pack), open the picker, verify all playable files render, pick a non-default
   one, verify it plays from the right index.

Open question for design: keep files as a sub-page of the card, or as a true
modal overlay. Probably modal, to match the existing `playerOverlay` pattern.

Implementation hint: the existing card click handler in `templates/index.html`
already calls `/api/files/<hash>` somewhere (must, because it picks the largest
file) — find that code path and branch on `file_stats.length > 1`.
