"""/api/github-webhook contracts (v2.4 hardening).

Locks in:
- No configured secret → 503 fail-closed (was: fail-open, anyone could trigger
  git pull + service restart).
- Missing/forged/non-ASCII X-Hub-Signature-256 → 401.
- Valid HMAC + non-main ref → ignored, no pull.
- Valid HMAC + main ref → pull runs; restart scheduled only for code files.
- git pull failure → 500, no restart, stderr surfaced.

Source: 2026-07-27 full-project audit.
"""
import hashlib
import hmac
import json

import pytest


SECRET = "test-webhook-secret"


def _sign(body: bytes) -> str:
    return "sha256=" + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()


def _payload(ref="refs/heads/main", modified=None) -> bytes:
    return json.dumps({
        "ref": ref,
        "commits": [{"modified": modified or [], "added": [], "removed": []}],
    }).encode()


@pytest.fixture
def webhook_env(app, monkeypatch):
    """Configure the secret and stub out git/systemctl subprocess calls."""
    monkeypatch.setattr(app, "GITHUB_WEBHOOK_SECRET", SECRET)

    calls = {"run": [], "popen": []}

    class FakeCompleted:
        returncode = 0
        stdout = "Already up to date.\n"
        stderr = ""

    def fake_run(cmd, **kwargs):
        calls["run"].append(cmd)
        result = FakeCompleted()
        result.returncode = calls.get("pull_rc", 0)
        result.stderr = calls.get("pull_stderr", "")
        return result

    class FakeProc:
        pass

    def fake_popen(cmd, **kwargs):
        calls["popen"].append(cmd)
        return FakeProc()

    monkeypatch.setattr(app.subprocess, "run", fake_run)
    monkeypatch.setattr(app.subprocess, "Popen", fake_popen)
    return calls


@pytest.mark.smoke
class TestWebhook:
    def test_unconfigured_secret_fails_closed(self, client, app, monkeypatch):
        monkeypatch.setattr(app, "GITHUB_WEBHOOK_SECRET", "")
        r = client.post("/api/github-webhook", data=_payload())
        assert r.status_code == 503
        assert r.get_json()["ok"] is False

    def test_missing_signature_rejected(self, client, webhook_env):
        r = client.post("/api/github-webhook", data=_payload())
        assert r.status_code == 401
        assert "invalid signature" in r.get_json()["error"]
        assert webhook_env["run"] == []  # no pull attempted

    def test_forged_signature_rejected(self, client, webhook_env):
        r = client.post(
            "/api/github-webhook", data=_payload(),
            headers={"X-Hub-Signature-256": "sha256=" + "0" * 64},
        )
        assert r.status_code == 401
        assert webhook_env["run"] == []

    def test_non_ascii_signature_rejected_not_500(self, client, webhook_env):
        r = client.post(
            "/api/github-webhook", data=_payload(),
            headers={"X-Hub-Signature-256": "café"},
        )
        assert r.status_code == 401

    def test_invalid_json_with_valid_signature_400(self, client, webhook_env):
        body = b"not json {"
        r = client.post(
            "/api/github-webhook", data=body,
            headers={"X-Hub-Signature-256": _sign(body)},
        )
        assert r.status_code == 400
        assert "invalid json" in r.get_json()["error"]

    def test_non_main_ref_ignored(self, client, webhook_env):
        body = _payload(ref="refs/heads/feature-x")
        r = client.post(
            "/api/github-webhook", data=body,
            headers={"X-Hub-Signature-256": _sign(body)},
        )
        assert r.status_code == 200
        assert r.get_json()["status"] == "ignored"
        assert webhook_env["run"] == []

    def test_code_push_pulls_and_schedules_restart(self, client, webhook_env):
        body = _payload(modified=["app.py"])
        r = client.post(
            "/api/github-webhook", data=body,
            headers={"X-Hub-Signature-256": _sign(body)},
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "updated"
        assert data["restart_scheduled"] is True
        assert len(webhook_env["run"]) == 1  # git pull ran
        assert len(webhook_env["popen"]) == 1  # restart scheduled
        # Restart must target the real unit, not the old torrstream.service default
        assert "flask-wrapper.service" in " ".join(webhook_env["popen"][0])

    def test_docs_only_push_no_restart(self, client, webhook_env):
        body = _payload(modified=[".planning/STATE.md"])
        r = client.post(
            "/api/github-webhook", data=body,
            headers={"X-Hub-Signature-256": _sign(body)},
        )
        assert r.status_code == 200
        assert r.get_json()["restart_scheduled"] is False
        assert webhook_env["popen"] == []

    def test_pull_failure_returns_500_no_restart(self, client, webhook_env):
        webhook_env["pull_rc"] = 1
        webhook_env["pull_stderr"] = "error: Your local changes would be overwritten"
        body = _payload(modified=["app.py"])
        r = client.post(
            "/api/github-webhook", data=body,
            headers={"X-Hub-Signature-256": _sign(body)},
        )
        assert r.status_code == 500
        data = r.get_json()
        assert data["ok"] is False
        assert "local changes" in data["pull_stderr"]
        assert webhook_env["popen"] == []  # no restart on failed pull
