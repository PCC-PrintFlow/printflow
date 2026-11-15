from playwright.sync_api import sync_playwright
import json
html = "file://"+__import__("os").environ["PRINTFLOW_HTML"]
mats=[{"id":"m1","name":"PLA Basic","type":"filament","unit":"g","packPrice":19.99,"packQty":1000,"notes":""},
      {"id":"m2","name":"Silk PLA","type":"filament","unit":"g","packPrice":29.99,"packQty":1000,"notes":""},
      {"id":"m3","name":"PETG","type":"filament","unit":"g","packPrice":22.99,"packQty":1000,"notes":""},
      {"id":"m4","name":"Magnet 6x3mm","type":"magnet","unit":"each","packPrice":8.99,"packQty":100,"notes":""}]
catalog=[{"id":"p1","name":"Keychain","part":"PCC-KC-01","custPart":"ACM-1","price":6,"bom":[{"materialId":"m1","qty":12}],"printHours":0.75,"laborMin":2,"extraCost":0},
 {"id":"p2","name":"Sticker","part":"PCC-ST","custPart":"","price":2,"bom":[],"printHours":0,"laborMin":0,"extraCost":0},
 {"id":"p4","name":"Keychain Gift Kit","part":"PCC-KIT","custPart":"","price":15,"isKit":True,"kitItems":[{"productId":"p1","qty":2}],"bom":[{"materialId":"m4","qty":2}],"printHours":0,"laborMin":5,"extraCost":0}]
cust={"id":"c1","name":"Jane Smith","business":"Acme Quilting Co.","email":"j@a.t","phone":"1","street":"1 Main","city":"Fort Wayne","state":"IN","zip":"46802"}
def item(i,p,n,qty,done=""):
    return {"id":i,"productId":p,"name":n,"part":"","custPart":"","qty":qty,"baseColor":"Red","fontColor":"","additionalColors":"","needByDate":"2026-11-20","completedDate":done,"deliveredDate":"","prodStatus":"waitprint","notes":"","invoiceId":None,"invoicedAt":""}
orders=[{"id":"o1","orderNumber":"ORD-PCC-2026-0007","name":"Fair batch","orderDate":"2026-11-01","needByDate":"2026-11-25","status":"open","completedDate":"","customerId":"c1","customer":cust,
  "items":[item("i1","p1","Keychain",10,"2026-11-10"), item("i2","p2","Sticker",5), item("i3","p4","Keychain Gift Kit",3,"2026-11-10")],"notes":""}]
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1280,"height":900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify([d.cust])); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_settings_v1', JSON.stringify({nextOrderNum:10, invPrefix:'PCC', nextInvNum:1004, machineRate:0.3, laborRate:20, targetMargin:50})); }""", {"catalog":catalog,"cust":cust,"orders":orders,"mats":mats})
    pg.reload(); pg.wait_for_timeout(300)
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.locator("#orderListWrap tr", has_text="ORD-PCC-2026-0007").locator("[data-oedit]").click(); pg.wait_for_timeout(250)
    print("fil selects:", pg.eval_on_selector_all("select[data-ofil]","e=>e.map(x=>x.dataset.ofil+':'+x.options[x.selectedIndex].text)"))
    print("sticker row empty:", pg.eval_on_selector("[data-fil-for='i2']","e=>e.innerHTML===''"))
    print("i1 note default:", pg.inner_text("[data-fil-for='i1'] .of-fil-note"))
    pg.select_option("#oi-fil-i1-m1", "m2"); pg.wait_for_timeout(80)
    print("i1 note silk:", pg.inner_text("[data-fil-for='i1'] .of-fil-note").replace("\n"," | "))
    pg.select_option("#oi-fil-i3-m1", "m3"); pg.wait_for_timeout(80)
    print("i3 note petg:", pg.inner_text("[data-fil-for='i3'] .of-fil-note").replace("\n"," | "))
    pg.screenshot(path="n_order.png", full_page=True)
    pg.click("#saveOrderBtn"); pg.wait_for_timeout(150)
    so = json.loads(pg.evaluate("localStorage.getItem('pcc_orders_v1')"))[0]
    print("saved swaps:", [(i["id"], i.get("filamentSwaps")) for i in so["items"]])
    # reload persists
    pg.reload(); pg.wait_for_timeout(250)
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.locator("#orderListWrap tr", has_text="ORD-PCC-2026-0007").locator("[data-oedit]").click(); pg.wait_for_timeout(250)
    print("after reload:", pg.eval_on_selector_all("select[data-ofil]","e=>e.map(x=>x.dataset.ofil+':'+x.value)"))
    # print order form
    pg.click("#previewOrderBtn") if pg.locator("#previewOrderBtn").count() else None
    pg.wait_for_timeout(200)
    print("order print:", pg.eval_on_selector_all("#oItems tr","rs=>rs.map(r=>r.children[0].innerText.replace(/\\n/g,' / '))"))
    pg.evaluate("document.querySelectorAll('[id^=close]').forEach(b=>{ if(b.offsetParent) b.click(); })"); pg.wait_for_timeout(100)
    # invoice
    pg.click("[data-oselect='i1']"); pg.click("[data-oselect='i3']"); pg.click("#createInvFromOrderBtn"); pg.wait_for_timeout(300)
    print("inv lines:", pg.eval_on_selector_all("#lineItemsBody tr","rs=>rs.map(r=>r.querySelector('[data-field=name]').value+' @ '+r.querySelector('[data-field=price]').value+' | '+[...r.querySelectorAll('.inv-from')].map(x=>x.innerText).join(' ; '))"))
    print("profit:", pg.inner_text("#profitBody").replace("\n"," | ")[:400])
    pg.screenshot(path="n_invoice.png", full_page=True)
    pg.click("#saveInvoiceBtn"); pg.wait_for_timeout(150)
    inv = json.loads(pg.evaluate("localStorage.getItem('pcc_invoices_v1')"))[0]
    print("inv saved:", [(l["name"], l["price"], l.get("filamentSwaps")) for l in inv["lineItems"]])
    # invoiced card: select disabled, summary meta shows filament
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.locator("#orderListWrap tr", has_text="ORD-PCC-2026-0007").locator("[data-oedit]").click(); pg.wait_for_timeout(250)
    print("invoiced meta:", pg.inner_text("[data-card-for='i1'] .of-meta"))
    # product change clears swaps
    pg.select_option("#oi-fil-i2-m1" if pg.locator("#oi-fil-i2-m1").count() else "#oi-product-i2", "p1"); pg.wait_for_timeout(80)
    pg.select_option("#oi-fil-i2-m1","m2"); pg.wait_for_timeout(50)
    pg.select_option("#oi-product-i2","p2"); pg.wait_for_timeout(80)
    pg.select_option("#oi-product-i2","p1"); pg.wait_for_timeout(80)
    print("after product change:", pg.eval_on_selector("#oi-fil-i2-m1","e=>e.value"))
    pg.select_option("#oi-fil-i2-m1","m2"); pg.click("#saveOrderBtn"); pg.wait_for_timeout(100)
    # grouped view
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.click("text=Group items by status") ; pg.wait_for_timeout(150)
    print("group has filament:", pg.locator("#orderListWrap", has_text="Filament:").count()>0, pg.eval_on_selector_all("#orderListWrap .kit-contents","e=>e.map(x=>x.innerText)"))
    b.close()
print("ERRORS:", errs)
