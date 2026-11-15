from playwright.sync_api import sync_playwright
import json
exec(open('test_q.py').read().split('\nerrs=[]\n')[0])
# simulate the earlier version: x1 ticked for fair with fair price 4.25, x2 ticked without fair price
for c in catalog:
    if c["id"]=="x1": c["fair"]=True; c["fairPrice"]=4.25
    if c["id"]=="x2": c["fair"]=True; c["fairPrice"]=None
errs=[]
def grab(pg, sel, out):
    pg.evaluate("window.__name=null")
    pg.click(sel); pg.wait_for_timeout(1500)
    name=pg.evaluate("window.__name"); data=bytes(pg.evaluate("window.__pdf")); open("/tmp/"+out,"wb").write(data); return name,len(data)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1366,"height":900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify([d.cust])); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_settings_v1', JSON.stringify({nextOrderNum:10, invPrefix:'PCC', nextInvNum:1005, machineRate:0.3, laborRate:20, targetMargin:50})); }""", {"catalog":catalog,"cust":cust,"orders":orders,"mats":mats})
    pg.reload(); pg.wait_for_timeout(300)
    pg.evaluate("window.claude={use:async()=>({save:async(o)=>{ window.__name=o.filename; window.__pdf=Array.from(o.data); return {status:'saved'}; }})}")
    st=json.loads(pg.evaluate("localStorage.getItem('pcc_catalog_v1')"))
    print("migrated:", [(x["id"],x.get("catalog"),x["price"],"fair" in x) for x in st if x["id"] in ("x1","x2","x3","p1")])
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(150)
    print("main title:", pg.inner_text("#catPanelTitle"), "| rows:", pg.locator("#catalogListWrap tbody tr").count())
    pg.click("#catSwFair"); pg.wait_for_timeout(150)
    print("fair title:", pg.inner_text("#catPanelTitle"), "| intro:", pg.inner_text("#catPanelIntro"))
    print("fair rows:", pg.eval_on_selector_all("#catalogListWrap tbody tr","rs=>rs.map(r=>r.children[0].innerText+' '+r.children[4].innerText)"))
    print("custpart field hidden:", pg.eval_on_selector("#catCustPartField","e=>e.style.display"))
    # add a fair item
    pg.fill("#catName","Dragon keychain"); pg.fill("#catPart","FAIR-DRG"); pg.fill("#catPrice","8")
    pg.click("#catAddBtn"); pg.wait_for_timeout(200)
    print("editor catalog radio fair:", pg.is_checked("#pmCatFair"))
    pg.locator('[data-bm="qty"]').first.fill("15")
    pg.click("#pmSave"); pg.wait_for_timeout(200)
    print("fair rows after add:", pg.eval_on_selector_all("#catalogListWrap tbody tr","rs=>rs.map(r=>r.children[0].innerText)"))
    pg.screenshot(path="u_fair.png")
    # move x2 back to business via editor
    pg.locator("#catalogListWrap [data-editprod='x2']").first.click(); pg.wait_for_timeout(150)
    pg.check("#pmCatBusiness"); pg.click("#pmSave"); pg.wait_for_timeout(200)
    print("fair rows after move:", pg.eval_on_selector_all("#catalogListWrap tbody tr","rs=>rs.map(r=>r.children[0].innerText)"))
    # print + pdf
    pg.click("#printCatalogBtn"); pg.wait_for_timeout(200)
    print("print:", pg.inner_text("#catTitle"), pg.eval_on_selector_all("#catPrintItems tr","rs=>rs.map(r=>r.innerText.replace(/\\s+/g,' '))"))
    print("pdf:", grab(pg, "#pdfCatalogNowBtn", "u_fair.pdf"))
    pg.evaluate("document.getElementById('closeCatalogPreviewBtn').click()")
    pg.click("#catSwMain"); pg.wait_for_timeout(100)
    pg.click("#printCatalogBtn"); pg.wait_for_timeout(200)
    t=pg.eval_on_selector_all("#catPrintItems tr","rs=>rs.map(r=>r.innerText.replace(/\\s+/g,' '))")
    print("business print has fair items?:", any("Dragon" in r or "style 01" in r for r in t), "| has x2:", any("style 02" in r for r in t))
    pg.evaluate("document.getElementById('closeCatalogPreviewBtn').click()")
    # order picker
    pg.click("button[data-tab='neworder']"); pg.wait_for_timeout(150)
    print("picker groups:", pg.eval_on_selector("select.of-product","s=>[...s.querySelectorAll('optgroup')].map(g=>g.label+' ('+g.children.length+')')"))
    pg.reload(); pg.wait_for_timeout(300)
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(150)
    print("remembered view:", pg.inner_text("#catPanelTitle"))
    b.close()
print("ERRORS:", errs)
