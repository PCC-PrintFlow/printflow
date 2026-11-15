from playwright.sync_api import sync_playwright
import json
exec(open('snap.py').read().split("with sync_playwright()")[0])
items[2]["completedDate"]="2026-11-06"; items[2]["invoiceId"]="inv1"; items[2]["invoicedAt"]="2026-11-07"
customers.append({"id":"c2","name":"Bob Lee","business":"Lee Crafts","email":"","phone":"","street":"","city":"","state":"","zip":""})
o2 = {"id":"o2","orderNumber":"ORD-PCC-2026-0008","orderDate":"2026-11-05","needByDate":"2026-11-30","status":"open","completedDate":"","customerId":"c2","customer":customers[1],
      "items":[{"id":"j1","productId":"p2","name":"Business Card Holder (608 Bearing)","part":"PCC-BCH-02","custPart":"","qty":3,"baseColor":"Red","fontColor":"","additionalColors":"","needByDate":"","completedDate":"","prodStatus":"waitprint","notes":"","invoiceId":None,"invoicedAt":""}],"notes":""}
o3 = {"id":"o3","orderNumber":"ORD-PCC-2026-0009","orderDate":"2026-11-09","needByDate":"2026-12-01","status":"open","completedDate":"","customerId":"c1","customer":customers[0],
      "items":[{"id":"k1","productId":"p3","name":"Fabric Stack Tray 8x8","part":"PCC-FT-08","custPart":"ACM-9910","qty":5,"baseColor":"Blue","fontColor":"","additionalColors":"","needByDate":"","completedDate":"","prodStatus":"pendingdesign","notes":"","invoiceId":None,"invoicedAt":""}],"notes":""}
orders.extend([o2,o3])
inv=[{"id":"inv1","invoiceNumber":"INV-PCC-2026-1003","date":"2026-11-07","dueDate":"","status":"sent","event":"","customerId":"c1","customer":customers[0],"lineItems":[],"taxable":True,"taxRate":7,"subtotal":0,"taxAmount":0,"total":0,"notes":""}]
errs=[]
def nums(pg): return {o["orderNumber"]:[i["id"] for i in o["items"]] for o in json.loads(pg.evaluate("localStorage.getItem('pcc_orders_v1')"))}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1280,"height":900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify(d.customers)); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); localStorage.setItem('pcc_invoices_v1', JSON.stringify(d.inv)); localStorage.setItem('pcc_settings_v1', JSON.stringify({nextOrderNum:10, invPrefix:'PCC'})); }""", {"catalog":catalog,"customers":customers,"orders":orders,"inv":inv})
    pg.reload(); pg.wait_for_timeout(300)
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.locator("#orderListWrap tr", has_text="ORD-PCC-2026-0007").locator("[data-oedit]").click(); pg.wait_for_timeout(250)
    print("move links:", pg.eval_on_selector_all("[data-omove]","bs=>bs.map(b=>b.dataset.omove)"), "(invoiced i3 should be absent)")
    # 1) move i2 -> new order
    pg.click("[data-omove='i2']"); pg.wait_for_timeout(100)
    print("summary:", pg.inner_text("#mvItemSummary").replace("\n"," / "), "| new hint:", pg.inner_text("#mvNewHint"), "| delete-src shown:", pg.is_visible("#mvDeleteSourceWrap"))
    pg.screenshot(path="g_modal_new.png")
    pg.click("#mvConfirm"); pg.wait_for_timeout(250)
    print("toast:", pg.inner_text("#toast"))
    print("orders:", nums(pg))
    new = [o for o in json.loads(pg.evaluate("localStorage.getItem('pcc_orders_v1')")) if o["orderNumber"]=="ORD-PCC-2026-0010"][0]
    print("new order:", new["customer"]["business"], new["needByDate"], new["status"], "|", new["notes"], "| item status:", new["items"][0]["prodStatus"], new["items"][0]["baseColor"])
    print("editor shows:", pg.input_value("#orderNumber"), "cards:", pg.locator(".of-card").count())
    # 2) move i1 -> existing order of another customer, open dest
    pg.click("[data-omove='i1']"); pg.wait_for_timeout(100)
    pg.check("#mvDestExisting"); pg.wait_for_timeout(80)
    print("groups:", pg.eval_on_selector_all("#mvOrderList .mv-group","g=>g.map(x=>x.innerText)"), "| choices:", pg.eval_on_selector_all("#mvOrderList input","i=>i.length"))
    pg.locator("#mvOrderList input[value='o2']").check(); pg.wait_for_timeout(50)
    print("warn:", pg.inner_text("#mvCustWarn"))
    pg.fill("#mvSearch","0009"); pg.wait_for_timeout(50); print("search hits:", pg.locator("#mvOrderList input").count()); pg.fill("#mvSearch","")
    pg.locator("#mvOrderList input[value='o2']").check(); pg.check("#mvOpenDest")
    pg.screenshot(path="g_modal_existing.png")
    pg.click("#mvConfirm"); pg.wait_for_timeout(250)
    print("toast:", pg.inner_text("#toast"), "| editor now:", pg.input_value("#orderNumber"))
    print("orders:", nums(pg))
    # 3) move only item of 0009 into 0007 (which still has invoiced i3) with delete source
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.locator("#orderListWrap tr", has_text="ORD-PCC-2026-0009").locator("[data-oedit]").click(); pg.wait_for_timeout(250)
    pg.click("[data-omove='k1']"); pg.wait_for_timeout(100)
    print("delete-src shown:", pg.is_visible("#mvDeleteSourceWrap"), pg.inner_text("#mvDeleteSourceText"))
    pg.check("#mvDestExisting"); pg.locator("#mvOrderList input[value='o1']").check(); pg.click("#mvConfirm"); pg.wait_for_timeout(250)
    print("toast:", pg.inner_text("#toast"), "| editor now:", pg.input_value("#orderNumber"))
    print("orders:", nums(pg))
    # 4) unsaved new order -> move saves it first
    pg.click("#resetOrderFormBtn"); pg.wait_for_timeout(80); pg.click("#confirmOk"); pg.wait_for_timeout(100)
    pg.fill("#ordCustPicker","Lee"); pg.wait_for_timeout(80); pg.locator("#ordCustSuggestions div[data-cid]").first.dispatch_event("mousedown"); pg.wait_for_timeout(80)
    pg.locator("select.of-product").first.select_option("p1"); pg.wait_for_timeout(50)
    pg.click("#addOrderLineBtn"); pg.wait_for_timeout(50); pg.locator("select.of-product").nth(1).select_option("p3"); pg.wait_for_timeout(50)
    first_id = pg.eval_on_selector_all("[data-omove]","bs=>bs[0].dataset.omove")
    pg.click(f"[data-omove='{first_id}']"); pg.wait_for_timeout(150)
    print("unsaved order saved before move:", pg.input_value("#orderNumber") in nums(pg), "| hint:", pg.inner_text("#mvNewHint"))
    pg.click("#mvConfirm"); pg.wait_for_timeout(250)
    print("orders:", {k:len(v) for k,v in nums(pg).items()})
    b.close()
print("ERRORS:", errs)
