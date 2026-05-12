#!/usr/bin/env python3
"""E2E smoke check against the production TorrStream deployment.

Hits the public URL (no TorrServer admin creds needed from this side) and prints
a one-line PASS/FAIL for each endpoint plus a compact evidence line.

This script is ignored by the deployment checklist — it's a developer
convenience for 'is the box healthy right now?' checks.
"""
from __future__ import annotations

import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "https://tv.trikiman.shop"
UA = "TorrStreamProdSmoke/1.0"
TIMEOUT = 15


def fetch(path: str, method: str = "GET"):
    url = BASE + path
    t0 = time.time()
    try:
        req = Request(url, headers={"User-Agent": UA}, method=method)
        with urlopen(req, timeout=TIMEOUT) as r:
            body = r.read()
            return {
                "ok": True,
                "status": r.status,
                "headers": dict(r.headers),
                "body": body,
                "ms": int((time.time() - t0) * 1000),
            }
    except HTTPError as e:
        return {
            "ok": False,
            "status": e.code,
            "headers": dict(e.headers or {}),
            "body": e.read(),
            "ms": int((time.time() - t0) * 1000),
            "err": f"HTTP {e.code}",
        }
    except URLError as e:
        return {"ok": False, "status": 0, "body": b"", "ms": int((time.time() - t0) * 1000), "err": f"URLError: {e}"}
    except Exception as e:
        return {"ok": False, "status": 0, "body": b"", "ms": int((time.time() - t0) * 1000), "err": f"{type(e).__name__}: {e}"}


def p_json(r):
    try:
        return json.loads(r["body"].decode("utf-8", errors="replace"))
    except Exception:
        return None


def row(label, r, extra=""):
    state = "PASS" if r["ok"] and 200 <= r["status"] < 400 else "FAIL"
    ct = (r.get("headers") or {}).get("Content-Type", "")
    print(f"[{state}] {label:<18} {r['status']:>3} {r['ms']:>4}ms  ct={ct[:40]:<40} {extra}")
    return state == "PASS"


def main():
    results = []

    # 1. Shell
    r = fetch("/")
    ok = row("Shell", r, extra=f"bytes={len(r['body'])}")
    if ok:
        body = r["body"].decode("utf-8", errors="replace")
        has_vidstack = "vidstack" in body.lower()
        has_installbtn = "Установить" in body
        print(f"    shell: vidstack={has_vidstack} install_btn_ru={has_installbtn}")
    results.append(ok)

    # 2. Manifest
    r = fetch("/manifest.json")
    ok = row("Manifest", r)
    if ok:
        j = p_json(r)
        if j:
            print(f"    manifest: name={j.get('name')!r} display={j.get('display')!r} icons={len(j.get('icons',[]))}")
    results.append(ok)

    # 3. Service worker
    r = fetch("/sw.js")
    ok = row("Service Worker", r, extra=f"bytes={len(r['body'])}")
    results.append(ok)

    # 4. Lampa plugin (v1.1)
    r = fetch("/static/lampa-sync.js")
    ok = row("Lampa plugin", r, extra=f"bytes={len(r['body'])}")
    results.append(ok)

    # 5. Status
    r = fetch("/api/status")
    ok = row("Status", r)
    if ok:
        j = p_json(r) or {}
        ts = j.get("torrserver") or {}
        wr = j.get("wrapper") or {}
        print(f"    status: ts.ok={ts.get('ok')} ts.count={ts.get('torrent_count')} wrapper.positions={wr.get('position_entries')}")
    results.append(ok)

    # 6. Library
    r = fetch("/api/torrents")
    library_items = []
    ok = row("Library", r)
    if ok:
        j = p_json(r) or {}
        library_items = j.get("items") or []
        diag = (j.get("diagnostics") or {}).get("state")
        print(f"    library: items={len(library_items)} state={diag}")
    results.append(ok)

    # 7. Search
    r = fetch("/api/search?q=%D0%BC%D0%B0%D1%82%D1%80%D0%B8%D1%86%D0%B0")
    ok = row("Search", r)
    if ok:
        j = p_json(r) or {}
        res = j.get("Results") or j.get("results") or []
        prov = j.get("provider") or j.get("provider_state") or j.get("source")
        print(f"    search: results={len(res)} ok={j.get('ok')} provider={prov}")
    results.append(ok)

    # 8. Files of first torrent (if any)
    try:
        if library_items:
            first = library_items[0] if isinstance(library_items[0], dict) else {}
            h = first.get("hash") or first.get("Hash") or first.get("infohash") or first.get("hex")
            print(f"    library[0] keys={list(first.keys())[:10]}")
            if h:
                r = fetch(f"/api/files/{h}")
                ok = row("Files[first]", r, extra=f"hash={h[:12]}")
                if ok:
                    j = p_json(r) or {}
                    files = j.get("files") or j.get("items") or []
                    playable = [f for f in files if isinstance(f, dict) and (f.get("playable") or f.get("is_playable"))]
                    print(f"    files: total={len(files)} playable={len(playable)}")
                    if files and isinstance(files[0], dict):
                        print(f"    files[0] keys={list(files[0].keys())[:8]}")
                results.append(ok)
            else:
                print("    [skip] Files check - no hash key on library item")
        else:
            print("    [skip] Files check - empty library")
    except Exception as e:
        print(f"[FAIL] Files[first]   exception: {type(e).__name__}: {e}")
        results.append(False)

    # 9. CORS preflight on /api/position/* (v1.1)
    try:
        r = fetch("/api/position/ffffffffffffffffffffffffffffffffffffffff", method="OPTIONS")
        ac = (r.get("headers") or {})
        allow_origin = ac.get("Access-Control-Allow-Origin")
        allow_methods = ac.get("Access-Control-Allow-Methods")
        ok = (200 <= (r.get("status") or 0) < 400) and (allow_origin is not None)
        row("CORS /api/position", r, extra=f"allow-origin={allow_origin!r} methods={allow_methods!r}")
        results.append(ok)
    except Exception as e:
        print(f"[FAIL] CORS /api/position exception: {type(e).__name__}: {e}")
        results.append(False)

    passed = sum(1 for x in results if x)
    total = len(results)
    print(f"\n{passed}/{total} PASS")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
