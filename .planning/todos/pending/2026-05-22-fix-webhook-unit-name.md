---
created: 2026-05-22T01:30:00.000Z
title: Fix auto-deploy webhook to use real systemd unit name
area: ops
files:
  - app.py:818-905
---

## Problem

The github webhook route `github_webhook()` in `app.py` defaults
`TORRSTREAM_SERVICE` to `torrstream.service`. The actual systemd unit on the
Oracle production host (`158.101.214.234`, `vless-x86-2`) is named
**`flask-wrapper.service`**. As a result, the webhook's
`sudo systemctl restart {TORRSTREAM_SERVICE}` command silently fails — the
shell `sudo` exits non-zero but the `subprocess.Popen([..])` call returns
immediately and we never observe the failure.

Discovered 2026-05-22 during v2.3 Phase 1 deploy. The push of commit 9fb813c
landed on GitHub but never reached the Flask process on Oracle. SSH diagnosis
showed:

- `Unit torrstream.service could not be found.`
- Real running process (PID 147075, started May 16): `/opt/torrstream/venv/bin/python /opt/torrstream/app/app.py`
- Real unit: `flask-wrapper.service` (loaded, active, running, "TorrStream Flask Wrapper")

This means **NO webhook restart has succeeded in the wrapper's history**. v2.2
deploys appeared to work because the changes were frontend-only
(templates/index.html, static/lampa-sync.js — served from disk per request,
no Python restart needed). All Python-level changes shipped since the May 16
process start have been silently NOT loaded into the running process for ~6
days. Examples that were affected:

- v2.2 Plan 1.1 (hash validation, 404 logic) — ONLY took effect because
  someone manually restarted on/around May 16 (likely during the resume bug
  iterations that day). Subsequent Python changes haven't loaded.
- v2.3 Plan 01-01 — first push (9fb813c) sat on the server's git but never
  reached the Flask process until manual `systemctl restart flask-wrapper`
  via SSH.

## Solution

Robust:

1. Update the default in `app.py:820` from `torrstream.service` to
   `flask-wrapper.service` so the webhook works without env override.
2. Set `TORRSTREAM_SERVICE=flask-wrapper.service` in the systemd unit's
   `Environment=` directive on Oracle, even though the new default would also
   work — explicit beats implicit.
3. Add error handling around the systemctl restart: capture stderr/exit code
   from a `subprocess.run` (with timeout) instead of fire-and-forget
   `subprocess.Popen`. Surface failures via `app.logger.error` so future
   silently-failing restarts are visible in journalctl.
4. Optionally: emit a healthcheck POST to a known URL on Oracle after the
   restart, so a failing restart causes the webhook response to include the
   failure status. GitHub's delivery dashboard then shows it.
5. Add a smoke test: `pytest tests/integration -m e2e` includes a "push a
   no-op commit, wait 30s, verify HEAD on prod is updated" check. (Lower
   priority — manual verification suffices for now.)

Verification after fix: push a Python-only commit, wait <30s, hit any v2.x
endpoint that didn't exist in the previous version. Should return new
behavior, not 404.

## Why this is its own todo (not folded into v2.3 Phase 1)

The v2.3 phase scope was the parser shim. The deploy bug was discovered
during deploy debugging but the fix has its own surface (webhook handler +
systemd unit config + logging) and would expand the phase scope. Captured
here so v2.4 picks it up cleanly.
