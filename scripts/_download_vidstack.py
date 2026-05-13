"""Download Vidstack's with-layouts CDN bundle + all chunked dependencies locally.

Serves two purposes:
1. Self-hosting eliminates 2 extra DNS + TLS round-trips (cdn.jsdelivr.net, cdn.vidstack.io)
2. Same-origin asset load gets HTTP/2 multiplexing over the existing TLS session to tv.trikiman.shop

Output layout under static/vidstack/:
  vidstack.js                      -- the main entry (rewritten to local chunk paths)
  chunks/vidstack-*.js            -- each chunked import
  providers/vidstack-*.js         -- provider modules (video, hls, dash, etc.)
  css/theme.css, css/video.css    -- default layout styles

We rewrite the bundle and providers to point to local paths so the browser
doesn't chase back to jsDelivr.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

VERSION = "1.12.13"
BASE = f"https://cdn.jsdelivr.net/npm/vidstack@{VERSION}"
ICONS_HOST = "https://cdn.vidstack.io/icons"

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static" / "vidstack"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "chunks").mkdir(exist_ok=True)
(OUT / "providers").mkdir(exist_ok=True)
(OUT / "css").mkdir(exist_ok=True)


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "vidstack-mirror/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def walk_chunks(js_text: str) -> list[str]:
    """Return relative chunk paths referenced by `import "..."` statements."""
    return re.findall(r'import\s*"([^"]+)"', js_text)


def rewrite(js_text: str) -> str:
    """Rewrite imports so:
    - ./chunks/X.js -> /static/vidstack/chunks/X.js
    - ./providers/X.js -> /static/vidstack/providers/X.js
    - https://cdn.vidstack.io/icons -> /static/vidstack/icons (we'll noop that)
    """
    def repl(m: re.Match) -> str:
        path = m.group(1)
        if path.startswith("./chunks/"):
            return f'import"/static/vidstack/chunks/{path.split("/")[-1]}"'
        if path.startswith("./providers/"):
            return f'import"/static/vidstack/providers/{path.split("/")[-1]}"'
        if path == ICONS_HOST or path.startswith("https://cdn.vidstack.io/"):
            # Drop icons import entirely — fallback SVGs ship with the layout template
            return 'import"/static/vidstack/icons-noop.js"'
        return m.group(0)

    return re.sub(r'import\s*"([^"]+)"', repl, js_text)


def save(rel_path: str, data: bytes) -> None:
    out = OUT / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    print(f"  saved {rel_path} ({len(data):,}B)")


def main() -> None:
    # Icon noop so rewritten imports don't 404 — an empty module is enough
    save("icons-noop.js", b"// vidstack icons placeholder (self-host noop)\n")

    # 1. Main entry
    main_url = f"{BASE}/cdn/with-layouts/vidstack.js"
    print(f"fetching {main_url}")
    main_body = fetch(main_url).decode()
    chunks_to_fetch = set()
    for imp in walk_chunks(main_body):
        if imp.startswith("./chunks/"):
            chunks_to_fetch.add(imp.split("/")[-1])
    rewritten = rewrite(main_body)
    save("vidstack.js", rewritten.encode())

    # 2. Recursively walk chunks — each chunk can import more chunks or provider files
    all_chunks = set()
    all_providers = set()
    queue = list(chunks_to_fetch)
    while queue:
        name = queue.pop()
        if name in all_chunks:
            continue
        all_chunks.add(name)
        url = f"{BASE}/cdn/with-layouts/chunks/{name}"
        try:
            body = fetch(url).decode()
        except Exception as e:
            print(f"  ! failed chunk {name}: {e}")
            continue
        for imp in walk_chunks(body):
            if imp.startswith("./") and imp.endswith(".js"):
                fname = imp.split("/")[-1]
                if "/chunks/" in imp:
                    if fname not in all_chunks:
                        queue.append(fname)
                elif "/providers/" in imp:
                    all_providers.add(fname)
            elif imp.startswith("../providers/"):
                all_providers.add(imp.split("/")[-1])
        save(f"chunks/{name}", rewrite(body).encode())

    # 3. Fetch providers. Their chunks often re-reference chunks already pulled.
    for name in list(all_providers):
        url = f"{BASE}/cdn/with-layouts/providers/{name}"
        try:
            body = fetch(url).decode()
        except Exception as e:
            print(f"  ! failed provider {name}: {e}")
            continue
        for imp in walk_chunks(body):
            if imp.startswith("../chunks/"):
                fname = imp.split("/")[-1]
                if fname not in all_chunks:
                    # pull it
                    try:
                        chunk_body = fetch(f"{BASE}/cdn/with-layouts/chunks/{fname}").decode()
                        all_chunks.add(fname)
                        save(f"chunks/{fname}", rewrite(chunk_body).encode())
                    except Exception as e:
                        print(f"  ! failed late chunk {fname}: {e}")
        # Providers reference chunks with ../chunks/X.js — rewrite to /static/vidstack/chunks/X.js
        def repl_prov(m: re.Match) -> str:
            path = m.group(1)
            if path.startswith("../chunks/"):
                return f'import"/static/vidstack/chunks/{path.split("/")[-1]}"'
            if path.startswith("./") and "/chunks/" in path:
                return f'import"/static/vidstack/chunks/{path.split("/")[-1]}"'
            return m.group(0)
        body = re.sub(r'import\s*"([^"]+)"', repl_prov, body)
        save(f"providers/{name}", body.encode())

    # 4. CSS
    for css_name, cdn_rel in [
        ("theme.css", "player/styles/default/theme.css"),
        ("video.css", "player/styles/default/layouts/video.css"),
    ]:
        url = f"{BASE}/{cdn_rel}"
        print(f"fetching {url}")
        body = fetch(url)
        save(f"css/{css_name}", body)

    print(f"\nDone. {1 + len(all_chunks) + len(all_providers)} JS files, 2 CSS files.")


if __name__ == "__main__":
    main()
