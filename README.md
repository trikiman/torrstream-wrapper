# TorrStream

TorrStream is a self-hosted Flask wrapper around TorrServer.

It provides a browser UI for:
- browsing torrents from TorrServer
- searching jacred
- streaming and downloading files
- syncing watch progress across devices

The wrapper now exposes diagnostics-first endpoints and UI states so an empty library, an unreachable TorrServer, and an unavailable search provider are distinguishable.

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

Config is driven by environment variables in `app.py`:
- `TORRSERVER_URL`
- `TORRSERVER_USER`
- `TORRSERVER_PASS`
- `JACRED_URL`
- `JACRED_KEY`

## Status

This repo is set up as a brownfield GSD project with planning artifacts under `.planning/`.
