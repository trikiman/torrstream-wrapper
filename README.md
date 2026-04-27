# TorrStream

TorrStream is a self-hosted Flask wrapper around TorrServer.

It provides a browser UI for:
- browsing torrents from TorrServer
- searching jacred
- streaming and downloading files
- syncing watch progress across devices

The wrapper now exposes diagnostics-first endpoints and UI states so an empty library, an unreachable TorrServer, and an unavailable search provider are distinguishable.

The shell also exposes:
- an install affordance for PWA-capable browsers
- iPad/Safari install guidance
- search fallback states for cached or local-library matches when the upstream provider is unavailable

## Project Layout

- `app.py` - Flask backend and API routes
- `templates/index.html` - main frontend UI
- `static/` - manifest, service worker, icons
- `.planning/` - GSD project planning artifacts

## Runtime Notes

The wrapper depends on a reachable TorrServer instance.

Install dependencies with:

```bash
pip install -r requirements.txt
```

Run the smoke check helper against a local wrapper instance:

```bash
python scripts/smoke_check.py
```

Config is driven by environment variables in `app.py`:
- `TORRSERVER_URL`
- `TORRSERVER_USER`
- `TORRSERVER_PASS`
- `JACRED_URL`
- `JACRED_KEY`

## Status

_Auto-deploy verified: 

This repo is set up as a brownfield GSD project with planning artifacts under `.planning/`.
