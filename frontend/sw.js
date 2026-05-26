const CACHE_NAME = "comled-cache-v1";
const ASSETS_TO_CACHE = [
  "/",
  "/index.html",
  "/app.js",
  "/logo-light.png",
  "/logo-dark.png",
  "/icon-192.png",
  "/icon-512.png"
];

// Instalar el Service Worker y almacenar en caché los activos estáticos
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("[Service Worker] Caching app shell");
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Activar el Service Worker y limpiar cachés viejas
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log("[Service Worker] Clearing old cache", cache);
            return caches.delete(cache);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Estrategia de red con caída a caché (Network First) para llamadas dinámicas de la API
// y Caché First para recursos estáticos del app shell.
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Si la petición es para la API backend, usar red primero
  if (url.pathname.startsWith("/api/")) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match(event.request);
      })
    );
  } else {
    // Para estáticos, usar caché primero
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request);
      })
    );
  }
});
