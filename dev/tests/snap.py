import json, sys
from playwright.sync_api import sync_playwright
html = "file://"+__import__("os").environ["PRINTFLOW_HTML"]
catalog = [
 {"id":"p1","name":"Personalized Name Keychain","part":"PCC-KC-01","custPart":"ACM-7781","price":6},
 {"id":"p2","name":"Business Card Holder (608 Bearing)","part":"PCC-BCH-02","custPart":"","price":18},
 {"id":"p3","name":"Fabric Stack Tray 8x8","part":"PCC-FT-08","custPart":"ACM-9910","price":14},
]
customers=[{"id":"c1","name":"Jane Smith","business":"Acme Quilting Co.","email":"jane@acme.test","phone":"260-555-0101","street":"12 Main St","city":"Fort Wayne","state":"IN","zip":"46802"}]
items=[
 {"id":"i1","productId":"p1","name":"Personalized Name Keychain","part":"PCC-KC-01","custPart":"ACM-7781","qty":25,"baseColor":"Black","fontColor":"White","additionalColors":"","needByDate":"2026-11-20","completedDate":"2026-11-08","notes":"Names list emailed 11/2","invoiceId":None,"invoicedAt":""},
 {"id":"i2","productId":"p2","name":"Business Card Holder (608 Bearing)","part":"PCC-BCH-02","custPart":"","qty":4,"baseColor":"Silk Gold","fontColor":"","additionalColors":"Black spool","needByDate":"2026-11-20","completedDate":"","notes":"","invoiceId":None,"invoicedAt":""},
 {"id":"i3","productId":"p3","name":"Fabric Stack Tray 8x8","part":"PCC-FT-08","custPart":"ACM-9910","qty":10,"baseColor":"Teal","fontColor":"","additionalColors":"","needByDate":"2026-11-25","completedDate":"","notes":"Logo on side wall","invoiceId":None,"invoicedAt":""},
]
orders=[{"id":"o1","orderNumber":"ORD-PCC-2026-0007","orderDate":"2026-11-01","needByDate":"2026-11-25","status":"inprogress","completedDate":"","customerId":"c1","customer":customers[0],"items":items,"notes":"Ship together"}]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1280,"height":900})
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify(d.customers)); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); }""", {"catalog":catalog,"customers":customers,"orders":orders})
    pg.reload()
    pg.evaluate("loadOrderIntoForm && 0")  if False else None
    # open order via Order Forms tab Edit button
    pg.click("button[data-tab='orders']")
    pg.wait_for_timeout(300)
    pg.screenshot(path="orders_list.png", full_page=True)
    btns = pg.locator("#orderListWrap button, #orderListWrap a")
    btns.nth(0).click()
    pg.wait_for_timeout(400)
    pg.screenshot(path="editor_full.png", full_page=True)
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(200)
    pg.locator("#orderListWrap button").nth(1).click(); pg.wait_for_timeout(400)
    pg.screenshot(path="print_view.png", full_page=True)
    b.close()
