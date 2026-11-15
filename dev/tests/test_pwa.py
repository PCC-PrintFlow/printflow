# Tests the installable build: offline worker, downloads, print, push/pull with a fake GitHub API.
from playwright.sync_api import sync_playwright
import json, base64, subprocess, time, os, threading
exec(open('test_n.py').read().split('\nerrs=[]\n')[0])
srv = subprocess.Popen(["python3","-m","http.server","8765","--bind","127.0.0.1"], cwd=__import__("os").environ["PRINTFLOW_SITE"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(0.8)
URL = "http://127.0.0.1:8765/"
# --- fake GitHub ---
REMOTE = {"file": None, "sha": None, "private": True, "puts": 0}
def gh(route):
    req = route.request; u = req.url; auth = req.headers.get("authorization","")
    if auth != "Bearer good-token": return route.fulfill(status=401, body='{"message":"Bad credentials"}', headers={"Access-Control-Allow-Origin":"*"})
    H = {"Access-Control-Allow-Origin":"*", "Content-Type":"application/json"}
    if u.endswith("/repos/pachuck/printflow-data"):
        return route.fulfill(status=200, headers=H, body=json.dumps({"full_name":"pachuck/printflow-data","private":REMOTE["private"],"permissions":{"push":True}}))
    if "/contents/printflow-data.json" in u:
        if req.method == "GET":
            if REMOTE["file"] is None: return route.fulfill(status=404, headers=H, body='{"message":"Not Found"}')
            if "raw" in req.headers.get("accept",""): return route.fulfill(status=200, headers=H, body=REMOTE["file"])
            return route.fulfill(status=200, headers=H, body=json.dumps({"sha":REMOTE["sha"],"size":len(REMOTE["file"])}))
        if req.method == "PUT":
            b = json.loads(req.post_data)
            if REMOTE["file"] is not None and b.get("sha") != REMOTE["sha"]: return route.fulfill(status=409, headers=H, body='{"message":"conflict"}')
            REMOTE["file"] = base64.b64decode(b["content"]).decode("utf-8"); REMOTE["puts"] += 1; REMOTE["sha"] = "sha%d" % REMOTE["puts"]
            return route.fulfill(status=200, headers=H, body=json.dumps({"content":{"sha":REMOTE["sha"]}}))
    if req.method == "OPTIONS": return route.fulfill(status=204, headers={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"*","Access-Control-Allow-Methods":"GET,PUT"})
    return route.fulfill(status=404, headers=H, body='{}')
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    # ---------- Device A ("PC") ----------
    ctxA = b.new_context(viewport={"width":1366,"height":900}, accept_downloads=True, service_workers="allow")
    ctxA.route("https://api.github.com/**", gh)
    A = ctxA.new_page(); A.on("pageerror", lambda e: errs.append("A:"+str(e))); A.on("console", lambda m: errs.append("A:"+m.text) if m.type=="error" else None)
    A.goto(URL); A.wait_for_timeout(500)
    A.evaluate("""(d)=>{ localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify([d.cust])); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); }""", {"catalog":catalog,"cust":cust,"orders":orders,"mats":mats})
    A.reload(); A.wait_for_timeout(800)
    print("standalone:", A.evaluate("window.PCC_STANDALONE"), "| version:", A.evaluate("window.PCC_APP_VERSION"))
    print("sw controller:", A.evaluate("navigator.serviceWorker.controller ? 'yes' : 'no'"), "| manifest link:", A.evaluate("!!document.querySelector('link[rel=manifest]')"))
    print("print btn label:", A.inner_text("#printNowBtn"))
    # offline reload
    ctxA.set_offline(True); A.reload(); A.wait_for_timeout(800)
    print("offline load OK:", A.evaluate("document.title"), "| orders:", A.evaluate("JSON.parse(localStorage.getItem('pcc_orders_v1')).length"))
    ctxA.set_offline(False)
    # download: backup + order PDF
    A.click("button[data-tab='settings']"); A.wait_for_timeout(150)
    with A.expect_download() as dl: A.click("#exportDataBtn")
    print("backup download:", dl.value.suggested_filename)
    A.click("button[data-tab='orders']"); A.wait_for_timeout(150)
    with A.expect_download(timeout=8000) as dl2: A.locator("#orderListWrap [data-opdf]").first.click()
    pth = dl2.value.path(); print("pdf download:", dl2.value.suggested_filename, open(pth,"rb").read(5))
    # print: stub iframe print
    A.locator("#orderListWrap [data-oview]").first.click(); A.wait_for_timeout(200)
    A.evaluate("window.__printed=0; HTMLIFrameElement.prototype.__p=1;")
    A.evaluate("""()=>{ const orig = document.createElement; document.createElement = function(t){ const el = orig.call(document,t); if(String(t).toLowerCase()==='iframe'){ setTimeout(()=>{ try{ el.contentWindow.print = ()=>{ window.__printed++; }; }catch(e){} },0);} return el; }; }""")
    A.click("#printOrderNowBtn"); A.wait_for_timeout(700)
    print("print called:", A.evaluate("window.__printed"))
    A.evaluate("document.getElementById('closeOrderPreviewBtn') && document.getElementById('closeOrderPreviewBtn').click()")
    # sync setup + push
    A.click("button[data-tab='settings']"); A.wait_for_timeout(150)
    print("not-in-claude note hidden:", A.eval_on_selector("#syncNotInClaude","e=>getComputedStyle(e).display"))
    A.fill("#syncDevice","PC"); A.fill("#syncRepo","pachuck/printflow-data"); A.fill("#syncToken","bad-token")
    A.click("#syncTestBtn"); A.wait_for_timeout(500); print("bad token:", A.inner_text("#toast"))
    A.fill("#syncToken","good-token"); A.click("#syncTestBtn"); A.wait_for_timeout(500); print("test:", A.inner_text("#toast"))
    A.click("#syncPullBtn"); A.wait_for_timeout(600); print("pull empty:", A.inner_text("#toast"))
    A.click("#syncPushBtn"); A.wait_for_timeout(800); print("push:", A.inner_text("#toast"), "| puts:", REMOTE["puts"])
    print("status A:", A.inner_text("#syncStatus").replace("\n"," | "))
    print("token not in payload:", "good-token" not in REMOTE["file"], "| pcc_sync not in payload:", "pcc_sync" not in REMOTE["file"])
    # ---------- Device B ("iPad") ----------
    ctxB = b.new_context(viewport={"width":820,"height":1180}, accept_downloads=True)
    ctxB.route("https://api.github.com/**", gh)
    B = ctxB.new_page(); B.on("pageerror", lambda e: errs.append("B:"+str(e)))
    B.goto(URL); B.wait_for_timeout(800)
    B.click("button[data-tab='settings']"); B.wait_for_timeout(150)
    B.fill("#syncDevice","iPad"); B.fill("#syncRepo","pachuck/printflow-data"); B.fill("#syncToken","good-token")
    B.click("#syncPullBtn"); B.wait_for_timeout(700)
    print("B pull confirm:", B.inner_text("#confirmText")[:160])
    B.click("#confirmOk"); B.wait_for_timeout(400)
    print("B orders after pull:", B.evaluate("JSON.parse(localStorage.getItem('pcc_orders_v1')).length"), "| B token kept:", B.evaluate("JSON.parse(localStorage.getItem('pcc_sync_v1')).token==='good-token'"))
    # B logs a fair sale and pushes
    B.click("button[data-tab='fairs']"); B.wait_for_timeout(200); B.click("[data-fprice='5']"); B.wait_for_timeout(100)
    B.click("button[data-tab='settings']"); B.wait_for_timeout(150)
    print("status B dirty:", B.inner_text("#syncStatus").replace("\n"," | "))
    B.click("#syncPushBtn"); B.wait_for_timeout(800); print("B push:", B.inner_text("#toast"), REMOTE["puts"])
    # A (stale) tries to push -> warning
    A.click("#syncPushBtn"); A.wait_for_timeout(800)
    print("A stale push warning:", A.inner_text("#confirmTitle"), "|", A.inner_text("#confirmOk"))
    A.click("#confirmCancel")
    A.click("#syncPullBtn"); A.wait_for_timeout(700); A.click("#confirmOk"); A.wait_for_timeout(400)
    print("A fair sales after pull:", A.evaluate("JSON.parse(localStorage.getItem('pcc_fairs_v1')).current.sales.length"))
    # public repo warning
    REMOTE["private"] = False; A.click("#syncTestBtn"); A.wait_for_timeout(500); print("public warn:", A.inner_text("#toast")[:60])
    A.screenshot(path="pwa_settings.png", full_page=True)
    b.close()
srv.terminate()
print("ERRORS:", errs)
