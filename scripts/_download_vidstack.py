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


def fetch(url: str, retries: int = 3) -> bytes:
    """Fetch with simple retry/backoff because jsDelivr occasionally rate-limits."""
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "vidstack-mirror/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                import time
                time.sleep(2 ** attempt)
    raise last_err  # type: ignore[misc]


def walk_chunks(js_text: str) -> list[str]:
    """Return relative paths referenced by both static `import "..."` and dynamic `import("...")` calls."""
    static_imports = re.findall(r'import\s*"([^"]+)"', js_text)
    dynamic_imports = re.findall(r'import\(\s*"([^"]+)"\s*\)', js_text)
    return static_imports + dynamic_imports


def rewrite(js_text: str, source_dir: str = "root") -> str:
    """Rewrite both static and dynamic imports so:
    - ./chunks/X.js -> /static/vidstack/chunks/X.js
    - ./providers/X.js -> /static/vidstack/providers/X.js
    - ../chunks/X.js -> /static/vidstack/chunks/X.js
    - ../providers/X.js -> /static/vidstack/providers/X.js
    - bare ./vidstack-X.js: depends on source_dir (providers vs chunks)
    - https://cdn.vidstack.io/icons -> /static/vidstack/icons (we'll noop that)
    - https://cdn.jsdelivr.net/.../media-captions/... -> noop (rare path; not used by mp4)
    """
    def remap(path: str) -> str | None:
        if path.endswith(".js"):
            fname = path.rsplit("/", 1)[-1]
            if "/chunks/" in path:
                return f"/static/vidstack/chunks/{fname}"
            if "/providers/" in path:
                return f"/static/vidstack/providers/{fname}"
            # Bare relative import like "./vidstack-XXX.js" — context-dependent
            if re.match(r"^\.{1,2}/vidstack-[A-Za-z0-9_-]+\.js$", path):
                if source_dir == "providers":
                    return f"/static/vidstack/providers/{fname}"
                return f"/static/vidstack/chunks/{fname}"
        if path == ICONS_HOST or path.startswith("https://cdn.vidstack.io/"):
            return "/static/vidstack/icons-noop.js"
        # NOTE: do NOT noop https://cdn.jsdelivr.net/.../media-captions/...
        # That library IS used at runtime when subtitle/caption tracks are present
        # (and the constructor check inside Vidstack throws "t is not a constructor"
        # if we hand it our empty icons-noop module). The captions chunk is small
        # and loads from jsDelivr's same CDN that the rest of Vidstack came from
        # originally; users who need it pay one extra DNS+TLS but it doesn't block
        # video playback.
        return None

    def repl_static(m: re.Match) -> str:
        new = remap(m.group(1))
        return f'import"{new}"' if new else m.group(0)

    def repl_dynamic(m: re.Match) -> str:
        new = remap(m.group(1))
        return f'import("{new}")' if new else m.group(0)

    js_text = re.sub(r'import\s*"([^"]+)"', repl_static, js_text)
    js_text = re.sub(r'import\(\s*"([^"]+)"\s*\)', repl_dynamic, js_text)
    return js_text


def save(rel_path: str, data: bytes) -> None:
    out = OUT / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    print(f"  saved {rel_path} ({len(data):,}B)")


def main() -> None:
    # Icon noop so rewritten imports don't 404 — an empty module is enough
    save("icons-noop.js", b"// vidstack icons placeholder (self-host noop)\n")

    queue_chunks: set[str] = set()
    queue_providers: set[str] = set()
    fetched: set[str] = set()  # already-downloaded URLs

    def classify(imp: str, source_dir: str = "root") -> None:
        """Add imp to the right queue based on its path components.

        source_dir = "providers" means relative `./vidstack-X.js` is a sibling provider;
        source_dir = "chunks" means relative `./vidstack-X.js` is a sibling chunk;
        source_dir = "root" means we're parsing main vidstack.js.
        """
        if not imp.endswith(".js"):
            return
        fname = imp.rsplit("/", 1)[-1]
        if "/providers/" in imp:
            queue_providers.add(fname)
        elif "/chunks/" in imp:
            queue_chunks.add(fname)
        elif re.match(r"^\.{1,2}/vidstack-[A-Za-z0-9_-]+\.js$", imp):
            # Bare relative import: classify by the file's own directory
            if source_dir == "providers":
                queue_providers.add(fname)
            else:
                queue_chunks.add(fname)

    # 1. Main entry
    main_url = f"{BASE}/cdn/with-layouts/vidstack.js"
    print(f"fetching {main_url}")
    main_body = fetch(main_url).decode()
    for imp in walk_chunks(main_body):
        classify(imp, source_dir="root")
    save("vidstack.js", rewrite(main_body, source_dir="root").encode())
    fetched.add("vidstack.js")

    # 2. BFS over chunks (each chunk can pull more chunks AND providers)
    while True:
        pending = {n for n in queue_chunks if f"chunks/{n}" not in fetched}
        if not pending:
            break
        name = pending.pop()
        rel = f"chunks/{name}"
        url = f"{BASE}/cdn/with-layouts/chunks/{name}"
        try:
            body = fetch(url).decode()
        except Exception as e:
            print(f"  ! failed chunk {name}: {e}")
            fetched.add(rel)
            continue
        for imp in walk_chunks(body):
            classify(imp, source_dir="chunks")
        save(rel, rewrite(body, source_dir="chunks").encode())
        fetched.add(rel)

    # 3. Providers (each provider can pull more chunks AND sibling providers)
    while True:
        pending = {n for n in queue_providers if f"providers/{n}" not in fetched}
        if not pending:
            break
        name = pending.pop()
        rel = f"providers/{name}"
        url = f"{BASE}/cdn/with-layouts/providers/{name}"
        try:
            body = fetch(url).decode()
        except Exception as e:
            print(f"  ! failed provider {name}: {e}")
            fetched.add(rel)
            continue
        for imp in walk_chunks(body):
            classify(imp, source_dir="providers")
        save(rel, rewrite(body, source_dir="providers").encode())
        fetched.add(rel)

    # 4. Drain any chunks newly discovered while pulling providers
    while True:
        pending = {n for n in queue_chunks if f"chunks/{n}" not in fetched}
        if not pending:
            break
        name = pending.pop()
        rel = f"chunks/{name}"
        url = f"{BASE}/cdn/with-layouts/chunks/{name}"
        try:
            body = fetch(url).decode()
        except Exception as e:
            print(f"  ! failed late chunk {name}: {e}")
            fetched.add(rel)
            continue
        for imp in walk_chunks(body):
            classify(imp, source_dir="chunks")
        save(rel, rewrite(body, source_dir="chunks").encode())
        fetched.add(rel)

    # 5. Self-host the media-captions library too. Vidstack lazy-loads it from
    # cdn.jsdelivr.net as a dynamic import — when subtitles are referenced in
    # any code path. We mirror it under captions/ and rewrite the absolute
    # jsdelivr URL inside the bundle to point local. This avoids:
    # (a) DPI-throttled jsdelivr fetches on Russian networks,
    # (b) the "t is not a constructor" runtime error if jsdelivr is offline.
    captions_base = "https://cdn.jsdelivr.net/npm/media-captions@next/dist"
    captions_queue = ["prod.js"]
    captions_fetched: set[str] = set()
    while captions_queue:
        rel = captions_queue.pop()
        if rel in captions_fetched:
            continue
        captions_fetched.add(rel)
        url = f"{captions_base}/{rel}"
        try:
            print(f"fetching {url}")
            body = fetch(url).decode()
        except Exception as e:
            print(f"  ! failed captions {rel}: {e}")
            continue
        # Find relative imports inside this captions file
        for m in re.finditer(r'["\']\.{1,2}/([^"\']+\.js)["\']', body):
            sub = m.group(1)
            sub_path = re.sub(r'^[^/]*/', '', sub) if '/' in m.group(0)[2:m.start(1)+2] else sub
            # Compute absolute target relative to current file
            base_dir = "/".join(rel.split("/")[:-1])
            if m.group(0).startswith('"./') or m.group(0).startswith("'./"):
                target = f"{base_dir}/{sub}" if base_dir else sub
            else:  # ../
                target = sub
            target = target.lstrip("/")
            if target not in captions_fetched:
                captions_queue.append(target)
        save(f"captions/{rel}", body.encode())

    # Now rewrite all references to the jsdelivr captions URL inside our
    # already-saved chunks to point at the local copy.
    captions_local = "/static/vidstack/captions/prod.js"
    captions_jsdelivr = "https://cdn.jsdelivr.net/npm/media-captions@next/dist/prod.js"
    for rel in fetched:
        if not rel.endswith(".js"):
            continue
        path = OUT / rel
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if captions_jsdelivr in content:
            new_content = content.replace(captions_jsdelivr, captions_local)
            path.write_text(new_content, encoding="utf-8")
            print(f"  rewired captions URL in {rel}")

    # 6. CSS
    for css_name, cdn_rel in [
        ("theme.css", "player/styles/default/theme.css"),
        ("video.css", "player/styles/default/layouts/video.css"),
    ]:
        url = f"{BASE}/{cdn_rel}"
        print(f"fetching {url}")
        body = fetch(url)
        save(f"css/{css_name}", body)

    chunks_count = sum(1 for f in fetched if f.startswith("chunks/"))
    providers_count = sum(1 for f in fetched if f.startswith("providers/"))
    print(f"\nDone. main + {chunks_count} chunks + {providers_count} providers + 2 CSS files.")


if __name__ == "__main__":
    main()
