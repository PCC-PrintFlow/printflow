from playwright.sync_api import sync_playwright
exec(open('test_r.py').read().split('\nerrs=[]\n')[0])
for i in range(1,40):
    catalog.append({"id":"x%d"%i,"name":"Coaster style %02d"%i,"part":"PCC-CS-%02d"%i,"custPart":"","price":4+i%5,"bom":[],"printHours":0,"laborMin":0,"extraCost":0})
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
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify([d.cust])); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); localStorage.setItem('pcc_invoices_v1', JSON.stringify([d.inv])); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_settings_v1', JSON.stringify({nextOrderNum:10, invPrefix:'PCC', nextInvNum:1005, machineRate:0.3, laborRate:20, targetMargin:50})); }""", {"catalog":catalog,"cust":cust,"orders":orders,"mats":mats,"inv":inv})
    pg.reload(); pg.wait_for_timeout(300)
    pg.evaluate("window.claude={use:async()=>({save:async(o)=>{ window.__name=o.filename; window.__pdf=Array.from(o.data); return {status:'saved'}; }})}")
    pg.click("button[data-tab='invoices']"); pg.wait_for_timeout(100)
    pg.screenshot(path="s_invlist.png", clip={"x":248,"y":0,"width":1118,"height":330})
    print("inv list:", grab(pg, "#invoiceListWrap [data-pdf]", "s_inv.pdf"))
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    print("order list:", grab(pg, "#orderListWrap [data-opdf]", "s_ord.pdf"))
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(100)
    pg.click("#printCatalogBtn"); pg.wait_for_timeout(200)
    print("catalog:", grab(pg, "#pdfCatalogNowBtn", "s_cat.pdf"))
    b.close()
print("ERRORS:", errs)
