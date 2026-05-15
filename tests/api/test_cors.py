"""CORS contract tests.

Locks in:
- /api/position/* gets Access-Control-Allow-Origin: * (covered also in test_position).
- /static/* gets Access-Control-Allow-Origin: * — Lampa-side fetch needs this.
- /api/torrents and other API routes do NOT get global CORS (scoped to the
  endpoints actually consumed cross-origin).

Source: 2026-05-14 E2E audit + v2.2 Plan 1.2.
"""
import pytest


@pytest.mark.smoke
@pytest.mark.cors
class TestStaticCors:
    def test_lampa_sync_has_cors_origin(self, client):
        r = client.get("/static/lampa-sync.js")
        assert r.status_code == 200
        assert r.headers.get("Access-Control-Allow-Origin") == "*"

    def test_static_manifest_has_cors_origin(self, client):
        r = client.get("/static/manifest.json")
        assert r.status_code == 200
        assert r.headers.get("Access-Control-Allow-Origin") == "*"


@pytest.mark.smoke
@pytest.mark.cors
class TestApiCorsScope:
    def test_api_torrents_does_not_have_cors(self, client, mock_ts):
        # Library list isn't consumed cross-origin; no CORS needed.
        r = client.get("/api/torrents")
        # Either no header at all, or absent ACAO
        assert "Access-Control-Allow-Origin" not in r.headers

    def test_api_search_does_not_have_cors(self, client):
        r = client.get("/api/search?q=")
        assert "Access-Control-Allow-Origin" not in r.headers
