// Service worker minimo: tiene in memoria la pagina che contiene l'app, così l'icona si apre anche con la rete lenta.
// I dati arrivano sempre da Streamlit (l'iframe), che non passa di qui.
const CACHE = "refillo-v1";
const FILE = ["./", "index.html", "manifest.webmanifest", "icona-192.png", "icona-512.png", "apple-touch-icon.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((nomi) => Promise.all(nomi.filter((n) => n !== CACHE).map((n) => caches.delete(n))))
    .then(() => self.clients.claim()));
});

// prima la rete (così gli aggiornamenti arrivano subito), la copia in memoria solo se la rete non risponde
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET" || new URL(e.request.url).origin !== self.location.origin) return;
  e.respondWith(fetch(e.request).then((r) => {
    const copia = r.clone();
    caches.open(CACHE).then((c) => c.put(e.request, copia));
    return r;
  }).catch(() => caches.match(e.request)));
});
