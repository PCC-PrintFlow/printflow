from playwright.sync_api import sync_playwright
import json
exec(open('test_n.py').read().split('\nerrs=[]\n')[0])
# more products so the catalog spans pages; a second kit sharing Keychain; a loose product
for i in range(1,46):
    catalog.append({"id":"x%d"%i,"name":"Coaster style %02d"%i,"part":"PCC-CS-%02d"%i,"custPart":"","price":4+i%5,"bom":[],"printHours":0,"laborMin":0,"extraCost":0})
catalog.append({"id":"p5","name":"Craft Fair Bundle","part":"PCC-BUN","custPart":"","price":20,"isKit":True,"kitItems":[{"productId":"p1","qty":3},{"productId":"p2","qty":2}],"bom":[],"printHours":0,"laborMin":0,"extraCost":0})
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1366,"height":900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify([d.cust])); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_settings_v1', JSON.stringify({nextOrderNum:10, invPrefix:'PCC', nextInvNum:1004, machineRate:0.3, laborRate:20, targetMargin:50})); }""", {"catalog":catalog,"cust":cust,"orders":orders,"mats":mats})
    pg.reload(); pg.wait_for_timeout(300)
    pg.evaluate("window.claude={use:async()=>({save:async(o)=>{window.__exp=o.data;}})}")
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(200)
    rows = pg.eval_on_selector_all("#catalogListWrap tbody tr","rs=>rs.slice(0,9).map(r=>(r.className||'-')+': '+r.children[0].innerText.replace(/\\n/g,' / '))")
    print("catalog rows:"); [print("  ",r) for r in rows]
    pg.screenshot(path="q_catalog.png", clip={"x":248,"y":0,"width":1118,"height":900}, full_page=True)
    # printed catalog -> export -> pdf
    pg.click("#printCatalogBtn"); pg.wait_for_timeout(200)
    pg.click("#printCatalogNowBtn"); pg.wait_for_timeout(300)
    t = pg.evaluate("window.__exp"); open("/tmp/exp_cat.html","w").write(t)
    pg.evaluate("document.getElementById('closeCatalogPreviewBtn').click()")
    # order select optgroups
    pg.click("button[data-tab='neworder']"); pg.wait_for_timeout(200)
    print("order select groups:", pg.eval_on_selector("select.of-product","s=>[...s.querySelectorAll('optgroup')].map(g=>g.label+' => '+[...g.children].slice(0,4).map(o=>o.text).join(' | '))"))
    # choose a member from second group (Keychain under Craft Fair Bundle) works
    sel = pg.locator("select.of-product").first
    val = pg.eval_on_selector("select.of-product","s=>s.querySelectorAll('optgroup')[0].children[1].value")
    sel.select_option(val); pg.wait_for_timeout(100)
    print("picked:", pg.eval_on_selector("select.of-product","s=>s.options[s.selectedIndex].text"), "| meta:", pg.inner_text(".of-meta").replace("\n"," "))
    # invoice export pdf
    pg2 = b.new_page(); pg2.goto("file:///tmp/exp_cat.html"); pg2.wait_for_timeout(300)
    pg2.pdf(path="/tmp/cat.pdf", prefer_css_page_size=True)
    b.close()
print("ERRORS:", errs)
