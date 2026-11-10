"use strict";

const scope = new URL(self.registration.scope);
const offlinePage = new URL("offline.html", scope);
const cachePrefix = `sigda-offline:${scope.pathname}:`;
const cacheName = `${cachePrefix}v1`;

self.addEventListener("install", (event) => {
    event.waitUntil((async () => {
        const response = await fetch(offlinePage, {
            cache: "reload",
            credentials: "omit",
            redirect: "error",
        });
        if (!response.ok || !response.headers.get("Content-Type")?.includes("text/html")) {
            throw new Error("Page hors ligne SIGDA indisponible.");
        }
        const cache = await caches.open(cacheName);
        await cache.put(offlinePage, response);
        await self.skipWaiting();
    })());
});

self.addEventListener("activate", (event) => {
    event.waitUntil((async () => {
        const names = await caches.keys();
        const obsolete = names.filter((name) => name.startsWith(cachePrefix) && name !== cacheName);
        await Promise.all(obsolete.map((name) => caches.delete(name)));
        await self.clients.claim();
    })());
});

self.addEventListener("fetch", (event) => {
    const { request } = event;
    if (request.method !== "GET" || request.mode !== "navigate") return;
    const url = new URL(request.url);
    if (!url.href.startsWith(scope.href) || url.pathname.toLowerCase().endsWith(".pdf")) return;

    event.respondWith(fetch(request).catch(async () => {
        const cache = await caches.open(cacheName);
        return await cache.match(offlinePage) || Response.error();
    }));
});
