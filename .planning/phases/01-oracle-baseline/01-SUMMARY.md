---
phase: 01-oracle-baseline
milestone: v2.0
subsystem: infrastructure
tags: [oracle, ubuntu, torrserver, flask, caddy, systemd, migration]
provides:
  - Oracle host with swap, firewall open for 80/443/8090, full stack running
  - TorrServer MatriX.141 with plaintext auth
  - Flask wrapper systemd unit with env-loaded TorrServer credentials
  - Caddy :80 reverse proxy (auto_https off for staging)
  - Reboot-resilient stack
key-decisions:
  - "TorrServer accs.db uses plaintext JSON {user: pass}, not bcrypt (MatriX.141 behavior)"
  - "Port 80 taken over by Caddy; nginx disabled (was VLESS WS fronting, non-critical)"
  - "Port 443 reserved for xray VLESS Reality; DO NOT TOUCH in this phase"
  - "auto_https off until Phase 3 DNS cutover"
  - "Flask wrapper + TorrServer run as ubuntu user; Caddy as caddy user"
requirements-completed: [INFRA-01, INFRA-02, INFRA-03 (staging), SEC-01]
duration: 60min
completed: 2026-05-11
---

# Phase 1 Summary: Oracle Baseline

**Target:** Oracle `vless-x86-2` (`158.101.214.234`, Ubuntu 22.04, 1 OCPU / 1 GB RAM / 45 GB disk, `eu-amsterdam-1`)

**Outcome:** Full TorrStream stack (TorrServer → Flask wrapper → Caddy) running, surviving reboots, externally reachable on port 80 with the Lampa plugin served correctly.

## Accomplishments

- 4 GB swap at `/swapfile`, persisted via `/etc/fstab`, `vm.swappiness=10` applied
- `iptables` INPUT chain accepts 8090 before the terminal REJECT, persisted via `iptables-persistent`
- TorrServer MatriX.141 binary at `/usr/local/bin/TorrServer`, systemd-managed, BasicAuth required (user: `torrstream`)
- Python 3.10 venv at `/opt/torrstream/venv` with `flask` and `requests`
- Flask wrapper at `/opt/torrstream/app/` from `trikiman/torrstream-wrapper` HEAD, systemd-managed, sends BasicAuth to TorrServer via env vars
- Caddy on port 80, reverse proxies to Flask :5000, gzip enabled, access log at `/var/log/torrstream/caddy-access.log`
- Reboot cycle verified — all 3 services auto-start

## Validation (external, from developer PC)

```
=== Probing http://158.101.214.234 via Caddy (port 80) ===
  /: HTTP 200 (text/html, 51856B)
  /api/status: HTTP 200 (torrserver.ok=true, torrent_count=0)
  /manifest.json: HTTP 200 (name=TorrStream)
  /sw.js: HTTP 200 (1540B)
  /static/lampa-sync.js: HTTP 200 (10046B)

=== TorrServer :8090 direct ===
  HTTP 401 Unauthorized (auth required, as intended)
```

## Files Created

- `/opt/torrstream/` tree and children (on host)
- `/var/lib/torrserver/accs.db` (on host, plaintext JSON)
- `/etc/torrstream/torrserver.env` (on host, 600 perms)
- `/etc/systemd/system/torrserver.service` (on host)
- `/etc/systemd/system/flask-wrapper.service` (on host)
- `/etc/caddy/Caddyfile` (on host)
- `/etc/sysctl.d/99-torrstream.conf` (on host)
- `scripts/_smoke_oracle.py` (repo, dev-only smoke probe)
- `.planning/phases/01-oracle-baseline/` (CONTEXT, 3 PLANs, HANDOFF, SUMMARY)

## Deviations from Plan

See `HANDOFF.md` → Deviations from Plan section. Four deviations, all recovered:

1. Port 80 was held by pre-existing nginx fronting VLESS WS — user confirmed non-critical, disabled nginx
2. TorrServer `accs.db` format is plaintext JSON, not bcrypt (plan assumption was wrong)
3. Caddy log dir permissions — pre-created log file with `caddy:caddy` ownership
4. Existing 2 GB swapfile was already present — resized in place to 4 GB

## Issues Encountered

- None that blocked completion. Two brief tool issues (long-running-command warning on `systemctl start` — resolved with `ignoreWarning: true`, and PowerShell heredoc quoting — worked around with bash heredocs).

## Next Phase Readiness

Phase 2 can begin. Open decisions captured in HANDOFF.md → Open Decisions for Phase 2.

---
*Phase 1 completed 2026-05-11 on Oracle `vless-x86-2` (158.101.214.234)*
