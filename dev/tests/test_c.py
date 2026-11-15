from playwright.sync_api import sync_playwright
import json, copy
exec(open('snap.py').read().split("with sync_playwright()")[0])
cust_old = {"name":"Jane Smith","email":"jane@acme.test","phone":"","street":"12 Main St","city":"Fort Wayne","state":"IN","zip":"46802"}  # no business, no phone
items[0]["prodStatus"]="inproduction"; items[0]["completedDate"]=""
items[1]["prodStatus"]="waitmaterial"
items[2]["prodStatus"]="pendingdesign"
o1 = orders[0]; o1["customer"]=dict(cust_old); o1["customerId"]="c1"
o2 = {"id":"o2","orderNumber":"ORD-PCC-2026-0008","orderDate":"2026-11-05","needByDate":"2026-11-12","status":"open","completedDate":"","customerId":None,
      "customer":{"name":"Bob Lee","business":"","email":"","phone":"","street":"","city":"","state":"","zip":""},
      "items":[{"id":"j1","productId":"p1","name":"Personalized Name Keychain","part":"PCC-KC-01","custPart":"ACM-7781","qty":50,"baseColor":"Red","fontColor":"White","additionalColors":"","needByDate":"2026-11-12","completedDate":"2026-11-09","prodStatus":"partial","notes":"","invoiceId":None,"invoicedAt":""},
               {"id":"j2","productId":"p3","name":"Fabric Stack Tray 8x8","part":"PCC-FT-08","custPart":"ACM-9910","qty":2,"baseColor":"Blue","fontColor":"","additionalColors":"","needByDate":"2026-11-08","completedDate":"","prodStatus":"waitmaterial","notes":"PETG","invoiceId":None,"invoicedAt":""}]}
orders.append(o2)
inv = {"id":"inv1","invoiceNumber":"INV-PCC-2026-1001","date":"2026-11-07","dueDate":"2026-12-07","status":"sent","event":"","customerId":None,"customer":{"name":"jane smith","business":"","email":"","phone":"","street":"","city":"","state":"","zip":""},"lineItems":[],"taxable":True,"taxRate":7,"subtotal":0,"taxAmount":0,"total":0,"notes":""}
customers=[{"id":"c1","name":"Jane Smith","business":"Acme Quilting Co.","email":"jane@acme.test","phone":"260-555-0101","street":"12 Main St","city":"Fort Wayne","state":"IN","zip":"46802"},
           {"id":"c2","name":"Bob Lee","business":"Lee Crafts","email":"bob@lee.test","phone":"260-555-0199","street":"","city":"Auburn","state":"IN","zip":""}]
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1280,"height":900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify(d.customers)); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); localStorage.setItem('pcc_invoices_v1', JSON.stringify(d.invoices)); }""", {"catalog":catalog,"customers":customers,"orders":orders,"invoices":[inv]})
    pg.reload(); pg.wait_for_timeout(600)
    print("toast:", pg.inner_text("#toast"))
    so = json.loads(pg.evaluate("localStorage.getItem('pcc_orders_v1')"))
    si = json.loads(pg.evaluate("localStorage.getItem('pcc_invoices_v1')"))
    print("o1 cust:", so[0]["customer"]); print("o2 cust:", so[1]["customer"], so[1]["customerId"]); print("inv cust:", si[0]["customer"], si[0]["customerId"])
    print("statuses:", [i["prodStatus"] for i in so[0]["items"]])
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(200)
    pg.screenshot(path="c_orders.png", full_page=True)
    pg.select_option("#orderStatusFilter","waitmaterial"); pg.wait_for_timeout(100)
    print("filtered rows (waitmaterial):", pg.locator("#orderListWrap tbody tr").count())
    pg.select_option("#orderStatusFilter","pendingdesign"); pg.wait_for_timeout(100)
    print("filtered rows (pendingdesign):", pg.locator("#orderListWrap tbody tr").count())
    pg.select_option("#orderStatusFilter",""); 
    pg.click("[data-olmode='group']"); pg.wait_for_timeout(200)
    print("group heads:", pg.eval_on_selector_all(".ofg-head", "hs=>hs.map(h=>h.innerText.replace(/\\n/g,' '))"))
    pg.screenshot(path="c_group.png", full_page=True)
    pg.select_option("#orderStatusFilter","waitmaterial"); pg.wait_for_timeout(100)
    print("group filtered:", pg.eval_on_selector_all(".ofg-head", "hs=>hs.map(h=>h.innerText.replace(/\\n/g,' '))"), "| rows:", pg.locator("#orderListWrap tbody tr").count())
    pg.locator("[data-oedit]").first.click(); pg.wait_for_timeout(300)
    print("opened order:", pg.input_value("#orderNumber"), "| cust card:", pg.inner_text("#ordCustSummary").replace("\n"," | "))
    print("i1 status:", pg.eval_on_selector("#oi-status-i1" ,"e=>e.options[e.selectedIndex].text") if pg.locator("#oi-status-i1").count() else "n/a")
    # persisted view mode
    pg.reload(); pg.wait_for_timeout(500); pg.click("button[data-tab='orders']"); pg.wait_for_timeout(200)
    print("view remembered:", pg.get_attribute("[data-olmode='group']","aria-pressed"), pg.input_value("#orderStatusFilter"))
    # customers tab + edit
    pg.click("button[data-tab='customers']"); pg.wait_for_timeout(200)
    pg.screenshot(path="c_customers.png", full_page=True)
    pg.locator("#customerListWrap [data-edit]").first.click(); pg.wait_for_timeout(100)
    pg.fill("#cePhone","260-555-7777"); pg.click("#ceSave"); pg.wait_for_timeout(200)
    print("edit toast:", pg.inner_text("#toast"))
    so = json.loads(pg.evaluate("localStorage.getItem('pcc_orders_v1')")); si=json.loads(pg.evaluate("localStorage.getItem('pcc_invoices_v1')"))
    print("phones:", so[0]["customer"]["phone"], si[0]["customer"]["phone"])
    # order print customer order
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.click("[data-olmode='orders']"); pg.wait_for_timeout(100)
    pg.select_option("#orderStatusFilter","")
    pg.locator("[data-oview]").last.click(); pg.wait_for_timeout(300)
    print("print cust block:", pg.inner_text("#oCustBusiness")+" | "+pg.inner_text("#oCustName")+" | "+pg.inner_text("#oCustPhone")+" | "+pg.inner_text("#oCustEmail")+" | "+pg.inner_text("#oCustAddress").replace("\n"," / "))
    pg.screenshot(path="c_print.png")
    b.close()
print("ERRORS:", errs)
