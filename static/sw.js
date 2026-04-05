// TorrStream Service Worker — offline shell caching
const CACHE_NAME = "torrstream-v1";
const SHELL_ASSETS = [
  "/app/",
  "/app/static/icons/icon-512.png",
  "https://cdn.plyr.io/3.7.8/plyr.css",
  "https://cdn.plyr.io/3.7.8/plyr.polyfilled.js",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS))
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
  if (url.pathname.startsWith("/app/api/")) {
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
