const CACHE_NAME = 'crm-campo-v4';
const OFFLINE_URLS = [
    '/campo/',
    '/campo/contato/',
    '/campo/interacao/',
    '/campo/checkin/',
    '/campo/cidade/',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(OFFLINE_URLS))
    );
    self.skipWaiting();
});

// Limpar caches antigos ao ativar
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // API POST requests: não cachear, tentar enviar e enfileirar se offline
    if (event.request.method !== 'GET') {
        event.respondWith(fetch(event.request).catch(() => {
            return new Response(JSON.stringify({ offline: true }), {
                status: 503,
                headers: { 'Content-Type': 'application/json' },
            });
        }));
        return;
    }

    // Network first para tudo — cache como fallback offline
    event.respondWith(
        fetch(event.request)
            .then((response) => {
                if (response.ok) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                }
                return response;
            })
            .catch(() => caches.match(event.request))
    );
});
