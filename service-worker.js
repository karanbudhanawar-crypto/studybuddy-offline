const CACHE='studybuddy-pwa-v6';
const SHELL=['./','./index.html','./manifest.webmanifest','./icon.svg'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET')return;const u=new URL(r.url);if(u.origin!==self.location.origin)return;e.respondWith(fetch(r).then(resp=>{if(resp&&resp.ok)caches.open(CACHE).then(c=>c.put(r,resp.clone()));return resp}).catch(()=>caches.match(r).then(c=>c||(r.mode==='navigate'?caches.match('./index.html'):Response.error()))))});