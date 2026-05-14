#!/usr/bin/env python3
"""TorrStream — Flask backend for cross-device torrent streaming with sync."""

import hashlib
import hmac
import json
import logging
import os
import re
import subprocess
import time
from pathlib import Path

import requests
from flask import Flask, Response, jsonify, redirect, request, send_from_directory, stream_with_context

app = Flask(__name__, static_folder="static", template_folder="templates")
app.logger.setLevel(logging.INFO)

# ─── Config ──────────────────────────────────────────────────────────────────
TORRSERVER = os.getenv("TORRSERVER_URL", "http://127.0.0.1:8090")
TORRSERVER_USER = os.getenv("TORRSERVER_USER", "")
TORRSERVER_PASS = os.getenv("TORRSERVER_PASS", "")
TORRSERVER_AUTH = (TORRSERVER_USER, TORRSERVER_PASS) if (TORRSERVER_USER or TORRSERVER_PASS) else None
JACRED_URL = os.getenv("JACRED_URL", "https://jac.red")
JACRED_KEY = os.getenv("JACRED_KEY", "")
POSITIONS_FILE = Path(__file__).parent / "positions.json"
RECENT_SEARCHES_FILE = Path(__file__).parent / "recent_searches.json"
RECENT_SEARCHES_LIMIT = 20

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".m4v", ".mov", ".wmv", ".ts", ".webm"}

# Infohash validation: SHA-1 (40 hex chars) or BTv2 SHA-256 (64 hex chars).
# Normalised to lowercase before any disk write or upstream call.
HASH_RE = re.compile(r"^[0-9a-fA-F]{40}$|^[0-9a-fA-F]{64}$")


# ─── Positions DB (file-based) ───────────────────────────────────────────────
def load_positions():
    """Load positions from JSON file. Schema:
    {
        "hash": {
            "files": {
                "1": {"position": 1234, "duration": 5000, "updated": 1711000000},
                "2": {"position": 0, "duration": 0, "updated": 0}
            },
            "last_file_index": 1,
            "updated": 1711000000
        }
    }
    """
    if POSITIONS_FILE.exists():
        try:
            data = json.loads(POSITIONS_FILE.read_text(encoding="utf-8"))
            # Migrate old flat format → new per-file format AND
            # normalise hash keys to lowercase (case-insensitive infohashes).
            migrated = {}
            for h, v in data.items():
                key = h.lower() if isinstance(h, str) else h
                if "files" in v:
                    migrated[key] = v
                else:
                    # Old format: {position, duration, updated}
                    migrated[key] = {
                        "files": {"1": {"position": v.get("position", 0), "duration": v.get("duration", 0), "updated": v.get("updated", 0)}},
                        "last_file_index": 1,
                        "updated": v.get("updated", 0),
                    }
            return migrated
        except (json.JSONDecodeError, AttributeError) as e:
            app.logger.warning("Failed to parse positions.json: %s", e)
            return {}
    return {}


def save_positions(data):
    tmp_file = POSITIONS_FILE.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_file.replace(POSITIONS_FILE)


# ─── Recent searches DB (file-based, server-synced across devices) ───────────
def load_recent_searches():
    """Load recent searches. Schema: {"queries": [{"q": str, "ts": int}, ...]}"""
    if RECENT_SEARCHES_FILE.exists():
        try:
            data = json.loads(RECENT_SEARCHES_FILE.read_text(encoding="utf-8"))
            queries = data.get("queries", [])
            cleaned = []
            for item in queries:
                if isinstance(item, dict) and isinstance(item.get("q"), str) and item["q"].strip():
                    cleaned.append({"q": item["q"], "ts": int(item.get("ts", 0))})
            return {"queries": cleaned}
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            app.logger.warning("Failed to parse recent_searches.json: %s", e)
    return {"queries": []}


def save_recent_searches(data):
    tmp_file = RECENT_SEARCHES_FILE.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_file.replace(RECENT_SEARCHES_FILE)


def record_recent_search(q):
    """Prepend query, dedupe (case-insensitive), cap at RECENT_SEARCHES_LIMIT."""
    q = (q or "").strip()
    if not q or len(q) > 200:
        return load_recent_searches()
    data = load_recent_searches()
    queries = [item for item in data.get("queries", []) if item.get("q", "").lower() != q.lower()]
    queries.insert(0, {"q": q, "ts": int(time.time())})
    data["queries"] = queries[:RECENT_SEARCHES_LIMIT]
    save_recent_searches(data)
    return data


# ─── TorrServer helpers ──────────────────────────────────────────────────────
def ts_post(path, payload=None):
    """POST to TorrServer with auth."""
    try:
        r = requests.post(f"{TORRSERVER}{path}", json=payload, auth=TORRSERVER_AUTH, timeout=10)
        r.raise_for_status()
        return r.json() if r.text.strip() else {}
    except Exception:
        return None


def ts_get(path, **kwargs):
    """GET from TorrServer with auth."""
    try:
        r = requests.get(f"{TORRSERVER}{path}", auth=TORRSERVER_AUTH, timeout=10, **kwargs)
        r.raise_for_status()
        return r
    except Exception:
        return None


def ts_probe():
    """Probe TorrServer reachability and basic library state."""
    try:
        r = requests.post(f"{TORRSERVER}/torrents", json={"action": "list"}, auth=TORRSERVER_AUTH, timeout=10)
        r.raise_for_status()
        data = r.json() if r.text.strip() else []
        torrent_count = len(data) if isinstance(data, list) else 0
        return {"ok": True, "torrent_count": torrent_count, "error": ""}
    except Exception as e:
        app.logger.warning("TorrServer probe failed: %s", e)
        return {"ok": False, "torrent_count": 0, "error": str(e)}


# ─── Hash validation helpers (v2.2 API hygiene) ──────────────────────────────
def _validate_hash(torrent_hash):
    """Validate an infohash from a route param.

    Returns:
        (lowercase_hash, None) if valid
        (None, (jsonify, 400)) otherwise — caller must `return err`.
    """
    if not torrent_hash or not HASH_RE.match(torrent_hash):
        return None, (jsonify({"ok": False, "error": "invalid hash"}), 400)
    return torrent_hash.lower(), None


def _torrent_exists(torrent_hash):
    """Check if TorrServer knows this hash.

    Returns:
        True  — torrent is in TS library
        False — TS reachable but torrent not present (genuine 404)
        None  — TS unreachable; cannot tell (caller should fall back to non-404 behavior)
    """
    result = ts_post("/torrents", {"action": "get", "hash": torrent_hash})
    if result is not None and result.get("hash"):
        return True
    # ts_post returned None (failure) or empty — distinguish "TS down" from "not found"
    probe = ts_probe()
    if not probe.get("ok"):
        return None
    return False


def normalize_torrent_link(raw_link):
    """Accept magnet links, HTTP URLs, and bare BTIH hashes."""
    link = (raw_link or "").strip()
    if not link:
        return None, "no link"

    if link.startswith("magnet:?"):
        return link, ""

    if link.startswith("http://") or link.startswith("https://"):
        return link, ""

    if re.fullmatch(r"[A-Fa-f0-9]{40}", link) or re.fullmatch(r"[A-Z2-7a-z2-7]{32}", link):
        return f"magnet:?xt=urn:btih:{link}", ""

    return None, "invalid link"


def get_viewed(torrent_hash):
    """Get list of viewed file indices from TorrServer."""
    result = ts_post("/viewed", {"action": "list", "hash": torrent_hash})
    if result and isinstance(result, list):
        return result
    return []


def get_all_viewed():
    """Get viewed entries for every torrent on TorrServer. Returns {hash: [file_index, ...]}."""
    # TorrServer requires hash key to be present (empty string returns all entries)
    result = ts_post("/viewed", {"action": "list", "hash": ""})
    if not (result and isinstance(result, list)):
        return {}
    viewed_map = {}
    for item in result:
        if not isinstance(item, dict):
            continue
        h = item.get("hash") or ""
        idx = item.get("file_index")
        if not h or idx is None:
            continue
        viewed_map.setdefault(h, []).append(idx)
    return viewed_map


def set_viewed(torrent_hash, file_index):
    """Mark file as viewed in TorrServer (so Lampa sees it too)."""
    result = ts_post("/viewed", {"action": "set", "hash": torrent_hash, "file_index": file_index})
    return result is not None


def probe_stream_access(filename, torrent_hash, file_index):
    """Check whether a stream request would succeed without returning the media body."""
    ts_url = f"{TORRSERVER}/stream/{filename}?link={torrent_hash}&index={file_index}&play"
    try:
        r = requests.get(ts_url, auth=TORRSERVER_AUTH, headers={"Range": "bytes=0-0"}, stream=True, timeout=20)
        try:
            content_type = r.headers.get("Content-Type", "")
            ok = r.status_code < 400
            return {
                "ok": ok,
                "upstream_status": r.status_code,
                "content_type": content_type,
                "error": "" if ok else f"upstream returned {r.status_code}",
            }
        finally:
            r.close()
    except Exception as e:
        return {
            "ok": False,
            "upstream_status": 0,
            "content_type": "",
            "error": str(e),
        }


# ─── API Routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory("static/icons", "icon-512.png", mimetype="image/png")


@app.route("/sw.js")
def service_worker():
    return send_from_directory("static", "sw.js", mimetype="application/javascript")


@app.route("/api/torrents")
def list_torrents():
    """List all torrents with merged position + viewed data."""
    result = ts_post("/torrents", {"action": "list"})
    if result is None:
        probe = ts_probe()
        return jsonify({
            "ok": False,
            "items": [],
            "error": probe.get("error", "torrserver error"),
            "diagnostics": {
                **probe,
                "state": "upstream_unavailable",
            },
        })

    torrents = result if isinstance(result, list) else []
    positions = load_positions()
    # Pull TorrServer's global "viewed" map so torrents watched in external
    # players (Lampa, etc) still surface in the "Continue" row even when the
    # wrapper hasn't recorded a position locally.
    viewed_map = get_all_viewed()

    enriched = []
    for t in torrents:
        h = t.get("hash", "")
        pos_data = positions.get(h, {})
        files_pos = pos_data.get("files", {})
        last_idx = pos_data.get("last_file_index", 0)

        # Get the last-played file's position for the "continue watching" bar
        last_pos = files_pos.get(str(last_idx), {})

        viewed_indices = viewed_map.get(h, [])

        t["position"] = last_pos.get("position", 0)
        t["duration"] = last_pos.get("duration", 0)
        t["last_file_index"] = last_idx
        t["updated"] = pos_data.get("updated", 0)
        t["viewed_in_torrserver"] = bool(viewed_indices)
        t["viewed_indices"] = viewed_indices
        enriched.append(t)

    return jsonify({
        "ok": True,
        "items": enriched,
        "diagnostics": {
            "ok": True,
            "torrent_count": len(enriched),
            "state": "empty" if not enriched else "ready",
            "error": "",
        },
    })


@app.route("/api/status")
def status():
    """Lightweight diagnostics for the wrapper shell."""
    positions = load_positions()
    return jsonify({
        "torrserver": {
            "url": TORRSERVER,
            **ts_probe(),
        },
        "search": {
            "url": JACRED_URL,
            "api_key_configured": bool(JACRED_KEY),
        },
        "wrapper": {
            "root": "/",
            "manifest": "/manifest.json",
            "service_worker": "/sw.js",
            "auth_configured": bool(TORRSERVER_AUTH),
            "position_entries": len(positions),
        },
    })


@app.route("/api/files/<torrent_hash>")
def list_files(torrent_hash):
    """Get file list for a torrent, enriched with viewed + position data."""
    torrent_hash, err = _validate_hash(torrent_hash)
    if err:
        return err

    result = ts_post("/torrents", {"action": "get", "hash": torrent_hash})
    if result is None:
        probe = ts_probe()
        # TS reachable but no such torrent → genuine 404. TS unreachable → 200 with state
        # so the existing UI's "upstream unavailable" empty state still renders.
        is_not_found = probe.get("ok") is True
        body = {
            "ok": False,
            "error": probe.get("error") or "torrent not found",
            "file_stats": [],
            "last_file_index": 0,
            "viewed_indices": [],
            "diagnostics": {
                **probe,
                "state": "not_found" if is_not_found else "upstream_unavailable",
                "playable_count": 0,
                "total_file_count": 0,
                "has_playable_files": False,
            },
        }
        return jsonify(body), (404 if is_not_found else 200)

    file_stats = result.get("file_stats") or []

    # Warmup fallback: migrated torrents (stat=5, "Torrent in db") sit in TorrServer's
    # db without being opened — their file_stats is empty until someone pings the /stream
    # endpoint. On cold start this showed up as "no video files" in the UI for every
    # torrent until the user manually clicked twice. Probe once with a 0-byte range
    # request; TorrServer opens the torrent, populates file_stats, then we re-GET.
    if not file_stats and result.get("hash"):
        name_parts = (result.get("name") or "movie").replace(" ", "%20")
        warmup_url = (
            f"{TORRSERVER}/stream/{name_parts}"
            f"?link={torrent_hash}&index=1&play"
        )
        try:
            requests.get(
                warmup_url,
                auth=TORRSERVER_AUTH,
                headers={"Range": "bytes=0-0"},
                timeout=6,
                stream=True,
            ).close()
        except Exception as e:
            app.logger.warning("list_files warmup failed for %s: %s", torrent_hash[:12], e)

        # Re-fetch after warmup so the caller gets real file_stats this request
        result = ts_post("/torrents", {"action": "get", "hash": torrent_hash}) or result
        file_stats = result.get("file_stats") or []

    positions = load_positions()
    pos_data = positions.get(torrent_hash, {})
    files_pos = pos_data.get("files", {})

    # Get viewed data from TorrServer (what Lampa has marked)
    viewed_list = get_viewed(torrent_hash)
    viewed_indices = set()
    for v in viewed_list:
        if isinstance(v, dict):
            viewed_indices.add(v.get("file_index", 0))
        elif isinstance(v, int):
            viewed_indices.add(v)

    for fs in file_stats:
        idx = str(fs.get("id", 0))
        fp = files_pos.get(idx, {})
        fs["position"] = fp.get("position", 0)
        fs["file_duration"] = fp.get("duration", 0)
        fs["viewed"] = fs.get("id", 0) in viewed_indices

        # If no explicit viewed flag but position > 95% of duration, count as viewed
        if fp.get("duration", 0) > 0 and fp.get("position", 0) / fp["duration"] > 0.95:
            fs["viewed"] = True

    # Filter to video files only
    video_files = []
    for fs in file_stats:
        path = fs.get("path", "")
        ext = os.path.splitext(path)[1].lower()
        if ext in VIDEO_EXTENSIONS or not ext:
            video_files.append(fs)

    return jsonify({
        "ok": True,
        "file_stats": video_files,
        "last_file_index": pos_data.get("last_file_index", 0),
        "viewed_indices": list(viewed_indices),
        "diagnostics": {
            "ok": True,
            "state": "no_playable_files" if not video_files and file_stats else "ready",
            "playable_count": len(video_files),
            "total_file_count": len(file_stats),
            "has_playable_files": bool(video_files),
            "error": "",
        },
    })


@app.after_request
def _cors_position(response):
    """Allow cross-origin position reads/writes (Lampa plugin lives on lampa.mx)."""
    if request.path.startswith("/api/position/"):
        response.headers.setdefault("Access-Control-Allow-Origin", "*")
        response.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type")
        response.headers.setdefault("Access-Control-Max-Age", "600")
    return response


@app.route("/api/position/<torrent_hash>", methods=["OPTIONS"])
def position_preflight(torrent_hash):
    # Preflight always succeeds — the actual GET/POST will validate the hash.
    # Returning 400 on preflight would break CORS for clients that haven't
    # verified the hash yet (browsers send OPTIONS before the real call).
    return ("", 204)


@app.route("/api/position/<torrent_hash>", methods=["GET"])
def get_position(torrent_hash):
    """Get watch position for a torrent (with optional file_index query param).

    Returns 404 only when the hash is unknown to BOTH the wrapper (no entry in
    positions.json) AND TorrServer's library. If the torrent IS known to TS but
    has no recorded position, returns 200 with zeros — preserves resume-on-play UX.
    """
    torrent_hash, err = _validate_hash(torrent_hash)
    if err:
        return err

    positions = load_positions()
    pos_data = positions.get(torrent_hash)

    if pos_data is None:
        # Cache miss — distinguish "never watched a known torrent" from "unknown hash"
        exists = _torrent_exists(torrent_hash)
        if exists is False:
            return jsonify({
                "ok": False,
                "error": "unknown hash",
                "position": 0,
                "duration": 0,
                "last_file_index": 1,
            }), 404
        # exists is True (known but no position) or None (TS unreachable) → fall through with zeros
        pos_data = {}

    file_index = request.args.get("file_index", str(pos_data.get("last_file_index", 1)))

    files_pos = pos_data.get("files", {})
    fp = files_pos.get(file_index, {})

    return jsonify({
        "ok": True,
        "position": fp.get("position", 0),
        "duration": fp.get("duration", 0),
        "last_file_index": pos_data.get("last_file_index", int(file_index)),
    })


@app.route("/api/position/<torrent_hash>", methods=["POST"])
def save_position(torrent_hash):
    """Save watch position. Body: {position, duration, file_index}."""
    torrent_hash, err = _validate_hash(torrent_hash)
    if err:
        return err

    body = request.get_json(force=True, silent=True) or {}
    try:
        pos = max(0, int(body.get("position", 0)))
        dur = max(0, int(body.get("duration", 0)))
        file_index_int = int(body.get("file_index", 1))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "invalid position payload"}), 400

    if file_index_int < 1:
        return jsonify({"ok": False, "error": "invalid file_index"}), 400

    file_index = str(file_index_int)
    now = int(time.time())

    positions = load_positions()
    if torrent_hash not in positions:
        positions[torrent_hash] = {"files": {}, "last_file_index": file_index_int, "updated": now}

    entry = positions[torrent_hash]
    if "files" not in entry:
        entry["files"] = {}

    entry["files"][file_index] = {"position": pos, "duration": dur, "updated": now}
    entry["last_file_index"] = file_index_int
    entry["updated"] = now

    viewed_sync_attempted = dur > 0 and pos / dur > 0.95
    viewed_synced = False
    # Auto-mark as viewed in TorrServer when > 95% watched
    if viewed_sync_attempted:
        viewed_synced = set_viewed(torrent_hash, file_index_int)

    try:
        save_positions(positions)
    except Exception as e:
        app.logger.warning("Failed to save positions: %s", e)
        return jsonify({"ok": False, "error": "failed to save position"}), 500

    return jsonify({
        "ok": True,
        "viewed_sync_attempted": viewed_sync_attempted,
        "viewed_synced": viewed_synced,
    })


@app.route("/api/stream/<path:filename>")
def stream(filename):
    """Proxy video stream from TorrServer with range support."""
    torrent_hash = request.args.get("hash", "")
    file_index = request.args.get("index", "1")
    probe_mode = request.args.get("probe") == "1"

    if not torrent_hash:
        return jsonify({"ok": False, "error": "missing hash"}), 400

    ts_url = f"{TORRSERVER}/stream/{filename}?link={torrent_hash}&index={file_index}&play"
    headers = {}
    if "Range" in request.headers:
        headers["Range"] = request.headers["Range"]

    if probe_mode:
        diagnostics = probe_stream_access(filename, torrent_hash, file_index)
        status_code = 200 if diagnostics["ok"] else 502
        return jsonify(diagnostics), status_code

    try:
        r = requests.get(ts_url, auth=TORRSERVER_AUTH, headers=headers, stream=True, timeout=30)
        if r.status_code >= 400:
            payload = {
                "ok": False,
                "error": f"stream request failed with {r.status_code}",
                "upstream_status": r.status_code,
                "content_type": r.headers.get("Content-Type", ""),
            }
            r.close()
            return jsonify(payload), 502

        resp_headers = {
            "Content-Type": r.headers.get("Content-Type", "video/mp4"),
            "Accept-Ranges": "bytes",
        }
        if "Content-Range" in r.headers:
            resp_headers["Content-Range"] = r.headers["Content-Range"]
        if "Content-Length" in r.headers:
            resp_headers["Content-Length"] = r.headers["Content-Length"]

        def generate():
            for chunk in r.iter_content(chunk_size=1024 * 256):
                yield chunk

        return Response(
            stream_with_context(generate()),
            status=r.status_code,
            headers=resp_headers,
        )
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "upstream_status": 0}), 502


@app.route("/api/add", methods=["POST"])
def add_torrent():
    """Add a torrent by magnet link or hash."""
    body = request.get_json(force=True, silent=True) or {}
    link, link_error = normalize_torrent_link(body.get("link", ""))
    title = body.get("title", "")
    poster = body.get("poster", "")

    if not link:
        return jsonify({"ok": False, "error": link_error or "no link"})

    payload = {"action": "add", "link": link, "title": title, "poster": poster, "save_to_db": True}
    result = ts_post("/torrents", payload)
    if result is not None:
        return jsonify({"ok": True, "hash": result.get("hash", ""), "normalized_link": link})
    return jsonify({"ok": False, "error": "torrserver add failed", "normalized_link": link})


@app.route("/api/remove/<torrent_hash>", methods=["DELETE"])
def remove_torrent(torrent_hash):
    """Remove a torrent. 404 when hash is unknown to both positions and TorrServer."""
    torrent_hash, err = _validate_hash(torrent_hash)
    if err:
        return err

    positions = load_positions()
    had_position = torrent_hash in positions

    # Existence check BEFORE remove — distinguish "removed" from "wasn't there"
    exists = _torrent_exists(torrent_hash)
    if not had_position and exists is False:
        return jsonify({
            "ok": False,
            "error": "unknown hash",
            "removed_positions": False,
        }), 404

    result = ts_post("/torrents", {"action": "rem", "hash": torrent_hash})
    positions.pop(torrent_hash, None)
    save_positions(positions)
    if result is None:
        # Distinguish from 404: torrent existed but TS rem failed → 502
        return jsonify({
            "ok": False,
            "error": "torrserver remove failed",
            "removed_positions": had_position,
        }), 502
    return jsonify({"ok": True, "removed_positions": had_position})


@app.route("/api/search")
def search():
    """Search via the configured Jacred-compatible provider.

    Handles two response shapes seen in the wild:
    - jac.red and current Jacred mirrors return a flat JSON list of torrent
      records ([{title, tracker, sid, magnet, ...}, ...]) or `{}` when there
      are no matches.
    - Older Jacred deployments returned a dict keyed by media id, where each
      value held a `torrents` array. Kept for backward compatibility.
    """
    q = request.args.get("q", "")
    if not q:
        return jsonify({"ok": True, "Results": []})

    try:
        params = {"search": q, "apikey": JACRED_KEY} if JACRED_KEY else {"search": q}
        r = requests.get(f"{JACRED_URL}/api/v1.0/torrents", params=params, timeout=15)
        data = r.json()
        results = []
        if isinstance(data, list):
            for torrent in data:
                if not isinstance(torrent, dict):
                    continue
                results.append({
                    "Title": torrent.get("title") or torrent.get("name", ""),
                    "Size": torrent.get("size", 0),
                    "Seeders": torrent.get("sid", 0),
                    "Tracker": torrent.get("tracker", ""),
                    "MagnetUri": torrent.get("magnet", ""),
                })
        elif isinstance(data, dict):
            for _key, item in data.items():
                if not isinstance(item, dict):
                    continue
                for torrent in item.get("torrents", []):
                    results.append({
                        "Title": torrent.get("title", item.get("title", "")),
                        "Size": torrent.get("size", 0),
                        "Seeders": torrent.get("sid", 0),
                        "Tracker": torrent.get("tracker", ""),
                        "MagnetUri": torrent.get("magnet", ""),
                    })
        return jsonify({"ok": True, "Results": results})
    except Exception as e:
        app.logger.warning("Search provider failed: %s", e)
        return jsonify({"ok": False, "Results": [], "error": str(e)})


@app.route("/api/recent-searches", methods=["GET"])
def get_recent_searches():
    """Return recent search queries (server-stored, synced across devices)."""
    return jsonify({"ok": True, **load_recent_searches()})


@app.route("/api/recent-searches", methods=["POST"])
def post_recent_search():
    """Record a search query. Body: {q: str}. Dedupes, caps at RECENT_SEARCHES_LIMIT."""
    body = request.get_json(force=True, silent=True) or {}
    q = body.get("q", "")
    if not isinstance(q, str) or not q.strip():
        return jsonify({"ok": False, "error": "missing query"}), 400
    return jsonify({"ok": True, **record_recent_search(q)})


@app.route("/api/recent-searches", methods=["DELETE"])
def clear_recent_searches():
    """Clear all recent searches."""
    save_recent_searches({"queries": []})
    return jsonify({"ok": True, "queries": []})


# ─── GitHub Webhook: auto-pull on push ───────────────────────────────────────
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
GIT_REPO_PATH = Path(__file__).parent
TORRSTREAM_SERVICE = os.getenv("TORRSTREAM_SERVICE", "torrstream.service")


@app.route("/api/github-webhook", methods=["POST"])
def github_webhook():
    """Receive GitHub push webhook, pull latest code, restart service.

    Mirrors the saleapp-backend pattern: verify HMAC signature, pull origin/main,
    restart the systemd unit if any code-relevant file changed.
    """
    body = request.get_data()

    # Verify signature when secret is configured
    if GITHUB_WEBHOOK_SECRET:
        sig_header = request.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(
            GITHUB_WEBHOOK_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig_header, expected):
            return jsonify({"ok": False, "error": "invalid signature"}), 401

    try:
        payload = json.loads(body)
    except Exception:
        return jsonify({"ok": False, "error": "invalid json"}), 400

    # Only act on pushes to main (ignore branch pushes, tag pushes, ping events)
    ref = payload.get("ref", "")
    if ref != "refs/heads/main":
        return jsonify({"ok": True, "status": "ignored", "ref": ref})

    # Backup runtime-state files before pull (defensive — protect them even
    # if skip-worktree gets cleared by some future git operation)
    runtime_backups = {}
    for runtime_file in (POSITIONS_FILE, RECENT_SEARCHES_FILE):
        if runtime_file.exists():
            try:
                runtime_backups[runtime_file] = runtime_file.read_text(encoding="utf-8")
            except Exception:
                pass

    pull_result = subprocess.run(
        ["git", "pull", "--ff-only", "origin", "main"],
        cwd=str(GIT_REPO_PATH),
        capture_output=True, text=True, timeout=30,
    )

    # Restore runtime-state files if pull touched them
    for runtime_file, backup in runtime_backups.items():
        try:
            current = runtime_file.read_text(encoding="utf-8") if runtime_file.exists() else ""
            if current != backup:
                runtime_file.write_text(backup, encoding="utf-8")
        except Exception as e:
            app.logger.warning("Failed to restore %s: %s", runtime_file.name, e)

    # Determine if any code files changed (so we know whether to restart)
    changed_files = []
    for c in payload.get("commits", []):
        changed_files.extend(c.get("modified", []))
        changed_files.extend(c.get("added", []))
        changed_files.extend(c.get("removed", []))

    code_changed = any(
        f.endswith(".py") or f.endswith(".html") or f.endswith(".js")
        or f.endswith(".css") or f == "requirements.txt"
        for f in changed_files
    )

    # Schedule a restart with a short delay so this response can flush back to
    # GitHub before systemd kills the worker. Popen returns immediately.
    if code_changed:
        subprocess.Popen(
            ["bash", "-c", f"sleep 2 && sudo systemctl restart {TORRSTREAM_SERVICE}"],
            cwd=str(GIT_REPO_PATH),
        )

    return jsonify({
        "ok": True,
        "status": "updated",
        "restart_scheduled": code_changed,
        "files_changed": len(changed_files),
        "pull_output": pull_result.stdout[:200],
        "pull_stderr": pull_result.stderr[:200] if pull_result.returncode != 0 else "",
    })


# ─── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Ensure directories exist
    (Path(__file__).parent / "templates").mkdir(exist_ok=True)
    (Path(__file__).parent / "static").mkdir(exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=False)
