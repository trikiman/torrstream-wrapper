"""/api/v1.0/torrents — Lampa parser shim contract tests (v2.3).

Locks in:
- Forwards all query params to JACRED_URL upstream verbatim.
- Returns upstream body byte-for-byte (Lampa parses jacred's native shape).
- 502 with empty-object body on upstream failure (so Lampa shows "no results"
  instead of a connection error).
- CORS Access-Control-Allow-Origin: * for cross-origin Lampa fetch.
- JACRED_KEY is auto-injected when configured and caller didn't include apikey.

Source: 2026-05-22 v2.3 LAMPA-01, LAMPA-02 — robust replacement for
manually flipping Lampa's `jackett_url` between jac.red mirrors when the
user's ISP blocks one of them.
"""
import json

import pytest


@pytest.mark.smoke
class TestLampaParserShim:
    def test_proxies_search_param_and_returns_raw_body(self, client, mocker):
        # Lampa hits /api/v1.0/torrents?search=Matrix and expects a flat array.
        upstream_body = [
            {"title": "The Matrix", "size": 1500000000, "sid": 200, "tracker": "rutor", "magnet": "magnet:?xt=urn:btih:abc"},
            {"title": "The Matrix Reloaded", "size": 2000000000, "sid": 50, "tracker": "rutracker", "magnet": "magnet:?xt=urn:btih:def"},
        ]
        fake = mocker.patch("requests.get")
        fake.return_value.status_code = 200
        fake.return_value.content = json.dumps(upstream_body).encode("utf-8")
        fake.return_value.headers = {"Content-Type": "application/json"}

        r = client.get("/api/v1.0/torrents?search=Matrix")
        assert r.status_code == 200
        # Body is the upstream array unchanged — NOT wrapped in {ok: true, Results: ...}
        data = r.get_json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["title"] == "The Matrix"
        assert data[0]["magnet"].startswith("magnet:?")

        # Verify upstream URL was correct
        called_url = fake.call_args[0][0]
        called_params = fake.call_args[1].get("params", {})
        assert called_url.endswith("/api/v1.0/torrents")
        assert called_params["search"] == "Matrix"

    def test_forwards_arbitrary_params(self, client, mocker):
        # Lampa may pass Query, title, year, is_serial, apikey, etc.
        fake = mocker.patch("requests.get")
        fake.return_value.status_code = 200
        fake.return_value.content = b"[]"
        fake.return_value.headers = {"Content-Type": "application/json"}

        client.get("/api/v1.0/torrents?Query=Pilot&title=Show&year=2026&is_serial=1")
        params = fake.call_args[1]["params"]
        assert params["Query"] == "Pilot"
        assert params["title"] == "Show"
        assert params["year"] == "2026"
        assert params["is_serial"] == "1"

    def test_empty_object_passthrough(self, client, mocker):
        # jacred returns `{}` for no results — must reach client unchanged.
        fake = mocker.patch("requests.get")
        fake.return_value.status_code = 200
        fake.return_value.content = b"{}"
        fake.return_value.headers = {"Content-Type": "application/json"}

        r = client.get("/api/v1.0/torrents?search=zzznoresults")
        assert r.status_code == 200
        assert r.get_data(as_text=True) == "{}"

    def test_upstream_failure_returns_502_empty_object(self, client, mocker):
        fake = mocker.patch("requests.get")
        fake.side_effect = Exception("connection refused")

        r = client.get("/api/v1.0/torrents?search=anything")
        assert r.status_code == 502
        # Lampa parses {} as "no results" — better UX than a parser-not-responding error.
        assert r.get_data(as_text=True) == "{}"

    def test_apikey_auto_injected_when_caller_omits_it(self, client, mocker, monkeypatch):
        # When wrapper has JACRED_KEY set and Lampa didn't pass apikey, ours is added.
        # JACRED_KEY is read at module import; reload + reapply after env override.
        import app as appmod
        monkeypatch.setattr(appmod, "JACRED_KEY", "wrapper-secret-key-123")

        fake = mocker.patch("requests.get")
        fake.return_value.status_code = 200
        fake.return_value.content = b"[]"
        fake.return_value.headers = {"Content-Type": "application/json"}

        client.get("/api/v1.0/torrents?search=Matrix")
        assert fake.call_args[1]["params"]["apikey"] == "wrapper-secret-key-123"

    def test_caller_apikey_preserved(self, client, mocker, monkeypatch):
        # If Lampa passes its own apikey, we don't overwrite it.
        import app as appmod
        monkeypatch.setattr(appmod, "JACRED_KEY", "wrapper-secret-key-123")

        fake = mocker.patch("requests.get")
        fake.return_value.status_code = 200
        fake.return_value.content = b"[]"
        fake.return_value.headers = {"Content-Type": "application/json"}

        client.get("/api/v1.0/torrents?search=Matrix&apikey=lampa-side-key")
        assert fake.call_args[1]["params"]["apikey"] == "lampa-side-key"


@pytest.mark.smoke
@pytest.mark.cors
class TestLampaParserShimCors:
    def test_cors_origin_set(self, client, mocker):
        fake = mocker.patch("requests.get")
        fake.return_value.status_code = 200
        fake.return_value.content = b"[]"
        fake.return_value.headers = {"Content-Type": "application/json"}

        r = client.get("/api/v1.0/torrents?search=anything")
        assert r.headers.get("Access-Control-Allow-Origin") == "*"

    def test_cors_methods_set(self, client, mocker):
        fake = mocker.patch("requests.get")
        fake.return_value.status_code = 200
        fake.return_value.content = b"[]"
        fake.return_value.headers = {"Content-Type": "application/json"}

        r = client.get("/api/v1.0/torrents?search=x")
        # Read-only proxy — only GET/HEAD/OPTIONS expected
        assert "GET" in r.headers.get("Access-Control-Allow-Methods", "")
