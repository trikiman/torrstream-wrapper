---
created: 2026-05-14T23:24:58.665Z
title: Add download UI per file in player/file-picker
area: ui
files:
  - templates/index.html:1077
  - app.py:498-555
---

## Problem

`README.md` claims TorrStream supports "streaming and downloading files", but the
template has zero download affordance:

- `grep -i "download|скачать|⬇|⤓|💾" templates/index.html` → 0 matches.
- The only `/api/stream/...` URL constructed in JS (line 1077) is for the
  Vidstack player; never wrapped in `<a download>`.
- The backend already supports it: `GET /api/stream/<filename>?hash=X&index=Y`
  proxies TorrServer with `Accept-Ranges: bytes`, so a plain anchor with the
  `download` attribute would just work.

This is a documented feature with no UI implementation. Confirmed via E2E audit
2026-05-14: clicking a card goes straight to player, no path to "save file
locally" anywhere in the UI.

## Solution

Robust (no quick fix):

1. Decide on UX: per-file row with a "Скачать" button, OR a download button
   inside the player chrome that mirrors the currently-selected file.
2. Probably best done together with the file-picker modal todo (multi-file UX),
   since both expose per-file affordances.
3. Render `<a class="file-download" href="/api/stream/<encoded-name>?hash=X&index=Y" download="<encoded-name>">` —
   `download` attribute forces save-as instead of inline play.
4. For mobile/iOS, add a fallback toast pointing at "Поделиться → Сохранить в
   Файлы" because Safari ignores `download` on cross-origin anchors.
5. Update `docs/SMOKE-TESTS.md` with a download verification step (single
   torrent, single file, byte-parity check vs the API).

Out of scope for this todo: changing how downloads are proxied; the backend
contract is fine as-is.
