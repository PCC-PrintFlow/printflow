"""Builds the installable PrintFlow app (what GitHub Pages serves) from dev/printflow.html.

    python3 dev/build.py

Writes these files at the repository root (overwriting them):
    index.html, sw.js, manifest.webmanifest, icon-192.png, icon-512.png,
    icon-maskable-512.png, apple-touch-icon.png
Never edit those by hand: edit dev/printflow.html and rebuild. Needs Pillow (pip install pillow).
dev/printflow.html itself runs as-is inside Claude (it is also the Claude artifact's page).
"""
import os, json, datetime
from PIL import Image
DEV = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DEV)
SRC = os.path.join(DEV, "printflow.html")
VERSION = datetime.datetime.now().strftime("%Y.%m.%d-%H%M")

mark = Image.open(os.path.join(DEV, "assets", "pcc-icon.png")).convert("RGBA")
def icon(size, frac, name):
    im = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    s = int(size * frac); m = mark.resize((s, s), Image.LANCZOS)
    im.alpha_composite(m, ((size - s) // 2, (size - s) // 2))
    im.convert("RGB").save(os.path.join(ROOT, name), optimize=True)
icon(192, 0.78, "icon-192.png")
icon(512, 0.78, "icon-512.png")
icon(512, 0.60, "icon-maskable-512.png")   # mark kept inside the 80% safe zone
icon(180, 0.78, "apple-touch-icon.png")

manifest = {
  "name": "PCC PrintFlow", "short_name": "PrintFlow",
  "description": "Pa Chuck Creations — orders, invoices, catalog, craft fairs",
  "id": "./", "start_url": "./", "scope": "./", "display": "standalone",
  "background_color": "#1c2220", "theme_color": "#1c2220",
  "icons": [
    {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
    {"src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}
  ]
}
with open(os.path.join(ROOT, "manifest.webmanifest"), "w") as f: json.dump(manifest, f, indent=2)

sw = """// PCC PrintFlow offline worker. Version: %(v)s
const CACHE = "printflow-%(v)s";
const ASSETS = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png"];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
// The app page: network first (so updates arrive), falling back to the saved copy after
// 4 seconds or when offline. Icons etc.: saved copy first. GitHub sync calls are never cached.
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  const isPage = req.mode === "navigate" || url.pathname.endsWith("/") || url.pathname.endsWith("index.html");
  if (isPage) {
    e.respondWith((async () => {
      const cache = await caches.open(CACHE);
      try {
        const net = await Promise.race([
          fetch(req, {cache: "no-store"}),
          new Promise((_, rej) => setTimeout(() => rej(new Error("slow")), 4000))
        ]);
        if (net && net.ok) { cache.put("index.html", net.clone()); return net; }
        throw new Error("bad response");
      } catch (err) {
        return (await cache.match("index.html")) || (await cache.match("./")) || Response.error();
      }
    })());
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
    if (res.ok) caches.open(CACHE).then(c => c.put(req, res.clone()));
    return res;
  })));
});
""" % {"v": VERSION}
with open(os.path.join(ROOT, "sw.js"), "w") as f: f.write(sw)

html = open(SRC, encoding="utf-8").read()
head_add = """
<meta name="theme-color" content="#1c2220">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="PrintFlow">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<script>window.PCC_STANDALONE = true; window.PCC_APP_VERSION = "%s";</script>
""" % VERSION
i = html.index("</title>") + len("</title>")
html = html[:i] + head_add + html[i:]
sw_reg = """<script>
if ("serviceWorker" in navigator) {
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("sw.js").catch(function (e) { console.warn("Offline mode unavailable", e); });
  });
}
</script>
"""
j = html.rindex("</body>")
html = html[:j] + sw_reg + html[j:]
with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f: f.write(html)
print("Built PrintFlow", VERSION, "into", ROOT)
