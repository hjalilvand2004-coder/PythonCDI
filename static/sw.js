// ═══════════════════════════════════════════════════════════
// Service Worker — PWA برای سامانه CDI
// کش کردن فایل‌های استاتیک برای اجرای آفلاین
// ═══════════════════════════════════════════════════════════
const CACHE_NAME = 'cdi-mobile-v1';
const STATIC_ASSETS = [
  '/',
  '/login',
  '/static/manifest.json',
  '/static/mobile.css',
  '/static/mobile.js',
  '/static/icons/icon.svg',
  'https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css',
];

// نصب — کش کردن فایل‌های پایه
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch(() => {});
    })
  );
  self.skipWaiting();
});

// فعال‌سازی — پاک کردن کش قدیمی
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.filter((name) => name !== CACHE_NAME).map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// fetch — استراتژی cache-first برای استاتیک، network-first برای صفحات
self.addEventListener('fetch', (event) => {
  const req = event.request;
  // فقط GET را کش کن
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  // صفحه‌های HTML → network-first (همیشه تازه)
  if (req.mode === 'navigate' || req.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(req).then((resp) => {
        const copy = resp.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
        return resp;
      }).catch(() => caches.match(req).then((r) => r || caches.match('/')))
    );
    return;
  }
  // فایل‌های استاتیک → cache-first
  if (url.origin === self.location.origin || url.hostname.includes('jsdelivr')) {
    event.respondWith(
      caches.match(req).then((cached) => {
        return cached || fetch(req).then((resp) => {
          if (resp.ok) {
            const copy = resp.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
          }
          return resp;
        }).catch(() => cached);
      })
    );
  }
});
