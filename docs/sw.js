// Offline cache for Hifz Recall. build.py stamps VERSION with a hash of the app files,
// so every deploy installs a fresh cache and removes the old one.
const VERSION = 'd5d7b69059fb';
const CACHE = 'hifz-' + VERSION;
const FILES = ['index.html', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'icon-maskable-512.png', 'apple-touch-icon.png'];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE)
      .then(cache => cache.addAll(FILES.map(f => new Request(f, { cache: 'reload' }))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k.startsWith('hifz-') && k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// The app's own files come from the cache; anything else (recitation audio from Quran.com) goes to the network.
self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const hit = await cache.match(req.mode === 'navigate' ? 'index.html' : req, { ignoreSearch: true });
    return hit || fetch(req);
  })());
});
