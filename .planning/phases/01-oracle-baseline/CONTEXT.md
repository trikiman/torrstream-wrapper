# Phase 1 Context: Oracle Baseline

**Goal:** Prepare Oracle `vless-x86-2` (`158.101.214.234`) to serve the full TorrStream stack (TorrServer → Flask → Caddy) from a staging hostname, matching the AWS topology but with an empty state. Phase 2 will migrate data onto this foundation.

**Milestone:** v2.0 Oracle Migration
**Requirements in scope:** INFRA-01, INFRA-02, INFRA-03, SEC-01

## Prior Context

- v1.0 + v1.1 shipped; production lives at AWS EC2 `13.60.174.46` with the topology Caddy → Flask → TorrServer
- `vless-x86-2` = fresh Ubuntu 22.04, 1 OCPU / 1 GB RAM / 45 GB disk, nothing installed beyond OS
- Only ports 22 / 80 / 443 accepted on the host firewall today. Ingress Security List entry for 8090 was added cloud-side but host nftables still drops it.
- `oracle-hunter` polling for ARM runs on the other instance (`vless-x86` @ 152.70.58.201). Do NOT touch it.

## Decisions (locked)

### D1 — SEC-01: How does Lampa reach TorrServer after migration?

**Decision:** Keep TorrServer exposed on port 8090 publicly, **enable TorrServer BasicAuth** (`--auth` with `accs.db`), and document credentials in a `.env`-style file outside the repo.

**Rationale:**
- Matches the AWS deployment behavior Lampa already works with (`http://<ip>:8090/stream/...?link=<hash>&index=<n>`)
- User selected "Open port 8090 on Oracle" in discuss pass. Accepting that tradeoff requires auth to prevent anonymous library manipulation.
- Proxying through Caddy would change Lampa stream URL pattern; plugin regex `/stream/.*?link=<hash>&index=<idx>` works either way, but changing the host means updating Lampa's TorrServer URL setting manually on every device. Simpler to keep the URL shape and add auth.

**Consequence for plan:** TorrServer systemd unit must pass `--auth /var/lib/torrserver/accs.db`. `accs.db` generated at provisioning time with one user. Credentials stored in `/etc/torrstream/torrserver.env` (root-owned, mode 600) and surfaced to the user post-phase.

### D2 — Staging access pattern

**Decision:** Use the **public IP with a self-signed pre-flight** for Phase 1 validation. No staging DNS record on `*.trikiman.shop`.

**Rationale:**
- DNS changes in this project are manual and we want Phase 3 DNS cutover to be a single operation.
- Caddy can issue a real Let's Encrypt cert once DNS points here, but until then we're blocked on validation because Let's Encrypt HTTP-01 needs the domain to resolve here.
- For Phase 1, the wrapper + TorrServer + Caddy reverse-proxy can be validated via direct IP + `curl -k`. Lampa plugin validation against staging is a Phase 2 task; by then we'll have a decision on how staging DNS works.

**Consequence for plan:** Caddyfile uses placeholder `tv.trikiman.shop` but with `auto_https off` so Caddy can start without a valid cert. Smoke check hits `http://158.101.214.234/api/status` directly until cutover.

### D3 — Swap size

**Decision:** 4 GB swap file at `/swapfile`, persisted in `/etc/fstab`.

**Rationale:**
- 1 GB RAM is tight for Python + TorrServer + Caddy + torrent piece cache
- 2 GB swap is the common recommendation for 1 GB RAM boxes; 4 GB gives headroom for jacred search spikes and torrent download bursts without thrashing
- 45 GB disk has plenty of space; 4 GB is ~9% of total

**Consequence for plan:** `fallocate -l 4G /swapfile` + `chmod 600` + `mkswap` + `swapon` + fstab entry. `vm.swappiness=10` to prefer RAM.

### D4 — Package sourcing

**Decision:** System package manager for Python/curl/unzip/Caddy; official GitHub release binary for TorrServer; pip for Python deps inside a `venv`.

**Rationale:**
- Caddy has an official `cloudsmith.io` apt repo with signing keys — use it
- TorrServer distributes as a single binary from `github.com/YouROK/TorrServer/releases` — simplest
- Flask wrapper deps (`flask`, `requests`) in a venv under `/opt/torrstream/venv` isolates from system Python

**Consequence for plan:** Plans 01-01 and 01-02 will fetch specific pinned versions (Caddy stable, TorrServer latest release tag) rather than floating latest.

### D5 — Systemd unit user

**Decision:** Run TorrServer and Flask wrapper as `ubuntu` user (not root, not a dedicated service user). Caddy runs as the `caddy` user from its package.

**Rationale:**
- Avoid the complexity of a new service user on a box that's also used for shell operations
- Matches simplicity of the personal-deployment project
- `/var/lib/torrserver` and `/opt/torrstream` owned by ubuntu, readable by appropriate users via group perms
- If this mattered more we'd isolate; for a personal server it's fine

**Consequence for plan:** Each systemd unit has `User=ubuntu`, `Group=ubuntu`, explicit `WorkingDirectory`, and `Restart=on-failure` with `RestartSec=10`.

### D6 — Phase 1 exit condition

**Decision:** Phase 1 is done when these can be demonstrated from the user's PC:
1. `curl -sk http://158.101.214.234/api/status` returns 200 JSON with `torrserver.ok: true` and zero torrents
2. `systemctl is-active torrserver flask-wrapper caddy` all return `active`
3. Reboot the Oracle box, all three services come back up
4. `ss -lntp` confirms 80, 443, 8090 bound (and 22 still)
5. TorrServer admin at `http://158.101.214.234:8090/` prompts for BasicAuth
6. Swap shows in `free -m`

No production domain on Oracle yet. Data migration is Phase 2.

## Open Questions (not blockers for Phase 1)

- **Q1 — staging DNS during Phase 2:** Do we create `tv-staging.trikiman.shop` for Phase 2 Lampa testing, or test Lampa against the raw IP? Decision deferred to Phase 2 discuss.
- **Q2 — TorrServer DB migration method:** Does a raw copy of `/var/lib/torrserver` between hosts preserve torrent state cleanly, or do we need to re-add torrents by magnet? Research in Phase 2.

## Reusable Assets from Prior Work

- `scripts/smoke_prod.py` — already probes shell, manifest, SW, status, library, search, Lampa plugin, CORS; will be used for Phase 3 verification as-is
- `docs/DEPLOYMENT.md` — AWS-specific but captures the Caddy + Flask + TorrServer pattern; model Oracle setup after it
- `docs/TORRSTREAM_DEPLOYMENT_CHECKLIST.md` — used in v1.0; adapt for Oracle in Phase 2

## Constraints for Phase 1 planner

- Do NOT touch the `oracle-hunter` service on `vless-x86`
- Do NOT touch any `saleapp`, `vless`, or unrelated projects' files on either box
- Do NOT change AWS EC2 configuration yet (still serving production)
- Do NOT change DNS records for `tv.trikiman.shop` in this phase
- Keep plans small: 2–3 plans total as scoped in ROADMAP.md

## Next: `/gsd-plan-phase 1`
