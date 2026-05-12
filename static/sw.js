// TorrStream Service Worker — offline shell caching
const CACHE_NAME = "torrstream-v4";
const SCOPE_PATH = new URL(self.registration.scope).pathname.replace(/\/$/, "");
const withBase = (path) => `${SCOPE_PATH}${path}` || path;
const API_PREFIX = withBase("/api/");
const SHELL_ASSETS = [
  withBase("/") || "/",
  withBase("/static/icons/icon-512.png"),
  "https://cdn.jsdelivr.net/npm/vidstack@1.12.13/player/styles/default/theme.css",
  "https://cdn.jsdelivr.net/npm/vidstack@1.12.13/player/styles/default/layouts/video.css",
  "https://cdn.jsdelivr.net/npm/vidstack@1.12.13/cdn/with-layouts/vidstack.js",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      // Add shell assets individually so one CDN hiccup (opaque response,
      // 5xx, network error) doesn't abort the whole install. We can still
      // serve these from network when the cache misses them.
      await Promise.all(
        SHELL_ASSETS.map(async (asset) => {
          try {
            const req = asset.startsWith("http")
              ? new Request(asset, { mode: "no-cors" })
              : asset;
            await cache.add(req);
          } catch (err) {
            // Swallow — offline shell is best-effort.
            console.warn("[sw] skip cache", asset, err && err.message);
          }
        })
      );
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((names) =>
      Promise.all(
        names.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);

  // Network-first for API calls and streams
  if (url.pathname.startsWith(API_PREFIX)) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
    return;
  }

  // Cache-first for shell assets
  e.respondWith(
    caches.match(e.request).then((cached) => {
      return cached || fetch(e.request).then((resp) => {
        // Cache successful responses
        if (resp.ok && e.request.method === "GET") {
          const clone = resp.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(e.request, clone));
        }
        return resp;
      });
    })
  );
});
