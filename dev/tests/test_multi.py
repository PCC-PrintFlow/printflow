from playwright.sync_api import sync_playwright
import json, os
exec(open('test_n.py').read().split('\nerrs=[]\n')[0])
catalog[0]["catalog"]="fair"   # keychain p1 ($6)
catalog.append({"id":"p5","name":"Dragon","part":"","custPart":"","price":10,"catalog":"fair","bom":[{"materialId":"m1","qty":20}],"printHours":1,"laborMin":0,"extraCost":0})
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1024,"height":1100})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_settings_v1', JSON.stringify({machineRate:0.3,laborRate:20,targetMargin:50,fairTaxRate:7,venmoFixed:0.09,venmoPct:2.29})); }""", {"catalog":catalog,"mats":mats})
    pg.reload(); pg.wait_for_timeout(300)
    pg.click("button[data-tab='fairs']"); pg.wait_for_timeout(200)
    assert pg.is_hidden("#fairCart")
    # normal one-tap sale still works
    pg.click("[data-fitem='p1']"); assert pg.inner_text("#fairCount").startswith("1 ")
    pg.click("#fairMultiBtn"); assert pg.is_visible("#fairCart")
    pg.click("[data-fitem='p5']"); pg.click("[data-fitem='p1']"); pg.click("[data-fitem='p1']"); pg.click("[data-fitem='p1']")
    pg.click("[data-fprice='3']")
    assert pg.inner_text("#fairCount").startswith("1 "), "nothing logged until Log"
    print("cart:", pg.inner_text("#fairCart").replace("\n"," | "))
    pg.click("[data-fcm='p1']")   # 3 -> 2 keychains
    assert "4 items · $25.00" in pg.inner_text("#fairCart")
    pg.screenshot(path="multi_cart.png")
    pg.click("#fairCartLog"); pg.wait_for_timeout(100)
    fs = json.loads(pg.evaluate("localStorage.getItem('pcc_fairs_v1')"))["current"]["sales"]
    print("sales:", fs[1])
    assert len(fs)==2 and fs[1]["price"]==25 and len(fs[1]["lines"])==3
    assert pg.is_enabled("#fairMultiBtn")
    t = pg.inner_text("#fairTotals").replace("\n"," | "); print(t)
    assert "Items sold | 5" in t and "Total collected (tax included) | $31.00" in t
    # fee charged once for the multi sale: 0.09+25*.0229 ; and single 0.09+6*.0229
    exp = round(0.09+25*0.0229 + 0.09+6*0.0229,2)
    assert ("$%.2f"%exp) in t, exp
    print("log row:", pg.inner_text("#fairLog .fl-log-row").replace("\n"," "))
    # toggle off + csv round trip
    pg.click("#fairMultiBtn"); assert pg.is_hidden("#fairCart")
    pg.evaluate("window.claude={use:async()=>({save:async(o)=>{ window.__csv=o.data; return {status:'saved'}; }})}")
    pg.click("#fairCsvBtn"); pg.wait_for_timeout(200)
    csv = pg.evaluate("window.__csv"); print([l for l in csv.splitlines() if "Dragon" in l])
    pg.screenshot(path="multi_log.png", full_page=True)
    print("OK")
print("ERRORS:", errs)
