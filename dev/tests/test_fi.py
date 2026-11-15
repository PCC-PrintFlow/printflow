from playwright.sync_api import sync_playwright
import json
exec(open('test_n.py').read().split('\nerrs=[]\n')[0])
catalog[0]["catalog"]="fair"
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1366,"height":1000})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); }""", {"catalog":catalog,"mats":mats})
    pg.reload(); pg.wait_for_timeout(300)
    pg.evaluate("window.claude={use:async()=>({save:async(o)=>{ (window.__saves=window.__saves||[]).push({name:o.filename, data: typeof o.data==='string'?o.data:Array.from(o.data)}); return {status:'saved'}; }})}")
    pg.click("button[data-tab='fairs']"); pg.wait_for_timeout(200)
    pg.set_input_files("#fairImportInput", "/tmp/deer-ridge.csv"); pg.wait_for_timeout(300)
    print("confirm:", pg.inner_text("#confirmTitle"), "|", pg.inner_text("#confirmText"), "|", pg.inner_text("#confirmOk"))
    pg.click("#confirmOk"); pg.wait_for_timeout(200)
    print("history:", pg.eval_on_selector_all("#fairHistory tbody tr:not(.fair-hist-detail)","rs=>rs.map(r=>r.innerText.replace(/\\s+/g,' '))"))
    pg.click("[data-fhview]"); pg.wait_for_timeout(100)
    print("details:", pg.inner_text(".fair-hist-detail").replace("\n"," | ")[:420])
    pg.screenshot(path="fi_hist.png", full_page=True)
    # re-export CSV from history and compare totals
    pg.click("[data-fhcsv]"); pg.wait_for_timeout(300)
    csv = pg.evaluate("window.__saves")[-1]["data"]
    print("re-export tail:\n" + "\n".join(csv.splitlines()[-8:]))
    # duplicate warning
    pg.set_input_files("#fairImportInput", "/tmp/deer-ridge.csv"); pg.wait_for_timeout(300)
    print("dup:", pg.inner_text("#confirmOk"), "|", pg.inner_text("#confirmText")[:80]); pg.click("#confirmCancel")
    # app-format CSV with Item column round trip
    open("/tmp/app.csv","w").write(csv.replace("Deer Ridge","Deer Ridge Copy"))
    pg.set_input_files("#fairImportInput", "/tmp/app.csv"); pg.wait_for_timeout(300); pg.click("#confirmOk"); pg.wait_for_timeout(200)
    print("rows now:", pg.locator("#fairHistory tbody tr:not(.fair-hist-detail)").count())
    # bad file
    open("/tmp/bad.csv","w").write("a,b\n1,2\n")
    pg.set_input_files("#fairImportInput", "/tmp/bad.csv"); pg.wait_for_timeout(300)
    print("bad toast:", pg.inner_text("#toast"))
    st=json.loads(pg.evaluate("localStorage.getItem('pcc_fairs_v1')"))
    h=st["history"][0]; print("stored:", h["name"], h["date"], len(h["sales"]), h["rates"], h["closedAt"], h["sales"][0])
    b.close()
print("ERRORS:", errs)
