from playwright.sync_api import sync_playwright
import json
exec(open('snap.py').read().split("with sync_playwright()")[0])
for c in catalog: pass
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1280,"height":900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify(d.customers)); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); }""", {"catalog":catalog,"customers":customers,"orders":orders})
    pg.reload(); pg.wait_for_timeout(400)
    # settings
    pg.click("button[data-tab='settings']"); pg.wait_for_timeout(100)
    pg.fill("#setMachineRate","0.30"); pg.fill("#setLaborRate","20"); pg.fill("#setTargetMargin","50"); pg.click("#saveSettingsBtn"); pg.wait_for_timeout(100)
    # materials
    pg.click("button[data-tab='materials']"); pg.wait_for_timeout(200)
    def addmat(name,typ,price,qty):
        pg.fill("#matName",name); pg.select_option("#matType",typ); pg.fill("#matPackPrice",price); pg.fill("#matPackQty",qty)
        hint = pg.inner_text("#matUnitCostHint"); pg.click("#matAddBtn"); pg.wait_for_timeout(80); return hint
    print("hint PLA:", addmat("PLA","filament","19.99","1000"))
    print("hint magnet:", addmat("Magnet 6x3mm N52","magnet","8.99","100"))
    addmat("M3x10 bolt","hardware","6.49","100"); addmat("M3 hex nut","hardware","4.99","100")
    print("materials rows:", pg.locator("#materialListWrap tbody tr").count())
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(150)
    print("summary:", pg.inner_text("#catMarginSummary"))
    # edit keychain: 12 g PLA, 0.75 h, 2 min labor
    pg.locator("[data-editprod='p1']").first.click(); pg.wait_for_timeout(150)
    pg.click("#pmAddLine"); pg.wait_for_timeout(50)
    bid = pg.eval_on_selector("#pmBom select[data-bm='materialId']","e=>e.dataset.bid")
    pg.select_option(f"#bm-mat-{bid}", label=pg.eval_on_selector(f"#bm-mat-{bid}","e=>[...e.options].find(o=>o.text.startsWith('PLA')).text"))
    pg.fill(f"#bm-qty-{bid}","12")
    pg.fill("#pmHours","0.75"); pg.fill("#pmLabor","2")
    print("pm summary:", pg.inner_text("#pmSummary").replace("\n"," | "))
    pg.click("#pmSave"); pg.wait_for_timeout(150)
    # tray: add product via add form -> modal with PLA prefilled, plus magnets via new-material quick add
    pg.fill("#catName","Magnetic Lid Box"); pg.fill("#catPart","PCC-MLB-01"); pg.fill("#catPrice","9"); pg.click("#catAddBtn"); pg.wait_for_timeout(150)
    print("new modal title:", pg.inner_text("#pmTitle"), "| prefilled lines:", pg.locator("#pmBom tbody tr").count())
    q = pg.locator("#pmBom input[data-bm='qty']").first; q.fill("60")
    pg.click("#pmNewMat summary"); pg.fill("#pmNmName","Magnet 10x2mm"); pg.select_option("#pmNmType","magnet"); pg.fill("#pmNmPrice","12"); pg.fill("#pmNmQty","50"); pg.click("#pmNmAdd"); pg.wait_for_timeout(100)
    q2 = pg.locator("#pmBom input[data-bm='qty']").nth(1); q2.fill("4")
    pg.fill("#pmHours","3"); pg.fill("#pmLabor","5"); pg.fill("#pmExtra","0.40")
    print("box summary:", pg.inner_text("#pmSummary").replace("\n"," | "))
    pg.screenshot(path="d_modal.png")
    pg.click("#pmSave"); pg.wait_for_timeout(150)
    print("catalog summary:", pg.inner_text("#catMarginSummary"))
    print("catalog rows:", pg.eval_on_selector_all("#catalogListWrap tbody tr","rs=>rs.map(r=>[...r.children].slice(0,6).map(c=>c.innerText).join(' / '))"))
    pg.screenshot(path="d_catalog.png", full_page=True)
    # invoice from order: mark keychain done + select + create invoice
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(150)
    pg.locator("#orderListWrap [data-oedit]").first.click(); pg.wait_for_timeout(250)
    pg.click("[data-oselect='i1']"); pg.wait_for_timeout(80)
    pg.click("#createInvFromOrderBtn"); pg.wait_for_timeout(300)
    print("profit:", pg.inner_text("#profitBody").replace("\n"," | "))
    # discount price below target
    pg.locator("#lineItemsBody input[data-field='price']").first.fill("3"); pg.wait_for_timeout(100)
    print("profit after discount:", pg.inner_text("#profitBody").replace("\n"," | "))
    pg.screenshot(path="d_invoice.png", full_page=True)
    pg.click("#saveInvoiceBtn"); pg.wait_for_timeout(200)
    saved = json.loads(pg.evaluate("localStorage.getItem('pcc_invoices_v1')"))
    print("saved line productId:", [l.get("productId") for l in saved[0]["lineItems"]])
    pg.click("button[data-tab='invoices']"); pg.wait_for_timeout(150)
    print("invoice list margin:", pg.eval_on_selector_all("#invoiceListWrap tbody tr","rs=>rs.map(r=>r.children[5].innerText)"))
    # material price change refreshes product cost
    pg.click("button[data-tab='materials']"); pg.wait_for_timeout(150)
    pg.locator("#materialListWrap [data-medit]").first.click(); pg.wait_for_timeout(80)
    pg.fill("tr[data-mrow] [data-mf='packPrice']","24.99"); pg.locator("[data-msave]").click(); pg.wait_for_timeout(120)
    print("after price change toast:", pg.inner_text("#toast"))
    # delete magnet material used in box
    # backup payload contains materials
    data = pg.evaluate("JSON.parse(localStorage.getItem('pcc_materials_v1')).length")
    print("stored materials:", data)
    b.close()
print("ERRORS:", errs)
