/* Service worker BaldCoaching : l'appli s'ouvre même sans réseau (salle en sous-sol, mode avion).
   - pages : réseau d'abord, copie locale si hors connexion ;
   - fichiers de l'appli et bibliothèque Supabase : copie locale, rafraîchie en arrière-plan ;
   - les échanges avec Supabase (données, connexion) ne sont jamais mis en cache ici. */
const V="bald-v1";
const SHELL=["/","/index.html","/config.js","/manifest.webmanifest","/icon-192.png","/icon-512.png","/apple-touch-icon.png","/favicon.png",
  "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.js"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(V).then(c=>Promise.allSettled(SHELL.map(u=>c.add(u)))).then(()=>self.skipWaiting()))});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{
  const r=e.request,u=new URL(r.url);
  if(r.method!=="GET")return;
  if(/supabase\.co$/.test(u.hostname))return;
  if(r.mode==="navigate"||u.pathname==="/config.js"){
    e.respondWith(fetch(r).then(res=>{const c=res.clone();caches.open(V).then(x=>x.put(r.mode==="navigate"?"/":r,c));return res}).catch(()=>caches.match(r.mode==="navigate"?"/":r).then(m=>m||caches.match("/index.html"))));return;
  }
  if(u.origin===location.origin||u.hostname==="cdn.jsdelivr.net"){
    e.respondWith(caches.match(r).then(m=>{const net=fetch(r).then(res=>{if(res.ok){const c=res.clone();caches.open(V).then(x=>x.put(r,c))}return res}).catch(()=>m);return m||net}));
  }
});
/* Notifications push (voir supabase/functions/notifier) */
self.addEventListener("push",e=>{let d={};try{d=e.data?e.data.json():{}}catch(_){d={body:e.data&&e.data.text()}}
  e.waitUntil(self.registration.showNotification(d.title||"BaldCoaching",{body:d.body||"",icon:"/icon-192.png",badge:"/favicon.png",data:{url:d.url||"/"},tag:d.tag||undefined}))});
self.addEventListener("notificationclick",e=>{e.notification.close();const url=(e.notification.data&&e.notification.data.url)||"/";
  e.waitUntil(self.clients.matchAll({type:"window",includeUncontrolled:true}).then(cs=>{for(const c of cs){if("focus" in c){c.navigate(url).catch(()=>{});return c.focus()}}return self.clients.openWindow(url)}))});
