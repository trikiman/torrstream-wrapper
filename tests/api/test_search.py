"""/api/search and /api/recent-searches contracts.

Locks in:
- Empty query returns `{ok: true, Results: []}` (200, not 400).
- Provider response variants (flat list vs dict-keyed-by-id) both transformed.
- Search failure (provider down) returns ok:false with error and empty Results.
- Recent searches CRUD: GET / POST / DELETE round-trip.
- POST recent with empty query returns 400.

Source: 2026-05-14 E2E audit Wave 1.3.
"""
import json

import pytest


@pytest.mark.smoke
class TestSearch:
    def test_empty_query_returns_empty_results(self, client):
        r = client.get("/api/search?q=")
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is True
        assert data["Results"] == []

    def test_no_query_param_returns_empty_results(self, client):
        r = client.get("/api/search")
        assert r.status_code == 200
        assert r.get_json()["Results"] == []

    def test_provider_flat_list_response_normalized(self, client, mocker):
        fake = mocker.patch("requests.get")
        fake.return_value.json.return_value = [
            {"title": "Matrix", "size": 1000000, "sid": 50, "tracker": "rutor", "magnet": "magnet:?xt=urn:btih:abc"},
        ]
        r = client.get("/api/search?q=matrix")
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is True
        assert len(data["Results"]) == 1
        item = data["Results"][0]
        assert item["Title"] == "Matrix"
        assert item["Seeders"] == 50
        assert item["MagnetUri"].startswith("magnet:?")

    def test_provider_dict_response_normalized(self, client, mocker):
        # Old jacred shape: keyed by media id
        fake = mocker.patch("requests.get")
        fake.return_value.json.return_value = {
            "603": {
                "title": "The Matrix",
                "torrents": [{"title": "The Matrix BDRip", "size": 5000000, "sid": 100, "tracker": "rutracker", "magnet": "magnet:?xt=urn:btih:def"}],
            },
        }
        r = client.get("/api/search?q=matrix")
        assert r.status_code == 200
        items = r.get_json()["Results"]
        assert len(items) == 1
        assert items[0]["Title"] == "The Matrix BDRip"
        assert items[0]["Tracker"] == "rutracker"

    def test_provider_failure_returns_ok_false(self, client, mocker):
        fake = mocker.patch("requests.get")
        fake.side_effect = Exception("connection refused")
        r = client.get("/api/search?q=matrix")
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is False
        assert data["Results"] == []
        assert "connection refused" in data["error"]


@pytest.mark.smoke
class TestRecentSearches:
    def test_empty_initial_state(self, client):
        r = client.get("/api/recent-searches")
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is True
        assert data["queries"] == []

    def test_post_get_round_trip(self, client):
        client.post("/api/recent-searches", json={"q": "matrix"})
        client.post("/api/recent-searches", json={"q": "пророк"})
        r = client.get("/api/recent-searches")
        queries = [q["q"] for q in r.get_json()["queries"]]
        assert "matrix" in queries
        assert "пророк" in queries
        # Newer queries appear first
        assert queries[0] == "пророк"

    def test_post_empty_query_returns_400(self, client):
        r = client.post("/api/recent-searches", json={"q": ""})
        assert r.status_code == 400
        assert "missing query" in r.get_json()["error"]

    def test_post_whitespace_query_returns_400(self, client):
        r = client.post("/api/recent-searches", json={"q": "   "})
        assert r.status_code == 400

    def test_post_dedupes(self, client):
        client.post("/api/recent-searches", json={"q": "matrix"})
        client.post("/api/recent-searches", json={"q": "matrix"})
        r = client.get("/api/recent-searches")
        queries = [q["q"] for q in r.get_json()["queries"]]
        assert queries.count("matrix") == 1

    def test_delete_clears_all(self, client):
        client.post("/api/recent-searches", json={"q": "matrix"})
        r = client.delete("/api/recent-searches")
        assert r.status_code == 200
        assert r.get_json()["queries"] == []
        # Confirm via GET
        r = client.get("/api/recent-searches")
        assert r.get_json()["queries"] == []
