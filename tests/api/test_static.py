"""Static asset and shell endpoint contracts.

Locks in:
- `/` returns HTML shell (50KB+ from a real build, but >5KB sanity floor).
- `/manifest.json` is valid JSON with `name`/`short_name`.
- `/sw.js` is JavaScript with the cache name marker.
- `/favicon.ico` returns image bytes (JPEG/PNG/ICO mimetype).
- `/static/lampa-sync.js` is reachable and contains the plugin's load marker.

Source: 2026-05-14 E2E feature audit, Wave 1.1.
"""
import pytest


@pytest.mark.smoke
class TestStaticAssets:
    def test_shell_returns_html(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "text/html" in r.headers["Content-Type"].lower()
        body = r.get_data(as_text=True)
        assert "<!DOCTYPE html>" in body or "<!doctype html>" in body.lower()
        assert "TorrStream" in body
        # Sanity: shell is the SPA, not a redirect / placeholder
        assert len(body) > 5000

    def test_manifest_is_valid_json(self, client):
        r = client.get("/manifest.json")
        assert r.status_code == 200
        assert "json" in r.headers["Content-Type"].lower()
        data = r.get_json()
        assert data["name"] == "TorrStream"
        assert "short_name" in data

    def test_service_worker_is_javascript(self, client):
        r = client.get("/sw.js")
        assert r.status_code == 200
        ct = r.headers["Content-Type"].lower()
        assert "javascript" in ct
        body = r.get_data(as_text=True)
        # SW must declare a cache name — otherwise install/activate is broken
        assert "CACHE_NAME" in body or "caches.open" in body

    def test_favicon_returns_image(self, client):
        r = client.get("/favicon.ico")
        assert r.status_code == 200
        ct = r.headers["Content-Type"].lower()
        assert ct.startswith("image/")

    def test_lampa_sync_script_is_reachable(self, client):
        r = client.get("/static/lampa-sync.js")
        assert r.status_code == 200
        body = r.get_data(as_text=True)
        # Plugin's loaded marker — both audit and integration tests rely on it
        assert "__torrstream_sync_loaded" in body
