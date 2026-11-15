from playwright.sync_api import sync_playwright
import json
exec(open('test_g.py').read().split("errs=[]")[0])
# o1 (Acme): i1 done; o3 (Acme): k1 done; o2 (Lee): j1 done. Legacy invoice inv1 covers i3 without line links.
orders[2]["items"][0]["completedDate"]="2026-11-10"
orders[1]["items"][0]["completedDate"]="2026-11-09"
inv[0]["lineItems"]=[{"name":"Fabric Stack Tray 8x8","part":"PCC-FT-08","custPart":"ACM-9910","qty":10,"price":14,"extended":140}]
inv[0]["sourceOrderId"]="o1"
errs=[]
def O(pg): return {o["orderNumber"]:{i["id"]:i.get("invoiceId") for i in o["items"]} for o in json.loads(pg.evaluate("localStorage.getItem('pcc_orders_v1')"))}
def INV(pg): return json.loads(pg.evaluate("localStorage.getItem('pcc_invoices_v1')"))
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1280,"height":900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify(d.customers)); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); localStorage.setItem('pcc_invoices_v1', JSON.stringify(d.inv)); localStorage.setItem('pcc_settings_v1', JSON.stringify({nextOrderNum:10, invPrefix:'PCC', nextInvNum:1004})); }""", {"catalog":catalog,"customers":customers,"orders":orders,"inv":inv})
    pg.reload(); pg.wait_for_timeout(300)
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.locator("#orderListWrap tr", has_text="ORD-PCC-2026-0007").locator("[data-oedit]").click(); pg.wait_for_timeout(250)
    pg.click("[data-oselect='i1']"); pg.click("#createInvFromOrderBtn"); pg.wait_for_timeout(300)
    print("toast:", pg.inner_text("#toast"))
    print("note:", pg.inner_text("#invSourceOrderNote"), "| event:", pg.input_value("#invEvent"))
    pg.click("#addFromOrdersBtn"); pg.wait_for_timeout(100)
    print("modal groups:", pg.eval_on_selector_all("#afoList .afo-order","g=>g.map(x=>x.innerText.replace(/\\n/g,' '))"))
    pg.check("#afoAllCust"); pg.wait_for_timeout(80)
    print("all-customers groups:", pg.eval_on_selector_all("#afoList .afo-order strong","g=>g.map(x=>x.innerText)"))
    pg.check("#afoList input[data-afo-i='j1']"); pg.wait_for_timeout(50); print("warn:", pg.inner_text("#afoWarn")); pg.uncheck("#afoList input[data-afo-i='j1']")
    pg.click("#afoList [data-afoall='o3']"); pg.wait_for_timeout(50); print("btn:", pg.inner_text("#afoAdd"))
    pg.screenshot(path="j_modal.png")
    pg.click("#afoAdd"); pg.wait_for_timeout(150)
    print("lines:", pg.eval_on_selector_all("#lineItemsBody tr","rs=>rs.map(r=>r.querySelector('input').value.slice(0,22)+' | '+(r.querySelector('.inv-from')||{innerText:''}).innerText)"))
    print("note:", pg.inner_text("#invSourceOrderNote"), "| event:", pg.input_value("#invEvent"))
    pg.click("#saveInvoiceBtn"); pg.wait_for_timeout(200)
    newinv = [i for i in INV(pg) if i["invoiceNumber"]!="INV-PCC-2026-1003"][0]
    print("saved sourceOrderIds:", newinv["sourceOrderIds"], "| line links:", [(l["orderId"], l["orderItemId"]) for l in newinv["lineItems"]])
    print("order items:", O(pg))
    pg.screenshot(path="j_invoice.png", full_page=True)
    # print shows order per line
    pg.click("button[data-tab='invoices']"); pg.wait_for_timeout(100)
    pg.locator("#invoiceListWrap tr", has_text=newinv["invoiceNumber"]).locator("[data-print]").click(); pg.wait_for_timeout(200)
    print("print lines:", pg.eval_on_selector_all("#pLineItems tr","rs=>rs.map(r=>r.children[0].innerText.replace(/\\n/g,' / '))"))
    pg.evaluate("document.getElementById('closePreviewBtn').click()"); pg.wait_for_timeout(100)
    # orders list shows the invoice on both orders
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    print("0009 invoiced cell:", pg.inner_text("#orderListWrap tr:has-text('0009') td >> nth=6").replace("\n"," "))
    # edit invoice, remove the k1 line, save -> k1 released
    pg.click("button[data-tab='invoices']"); pg.wait_for_timeout(100)
    pg.locator("#invoiceListWrap tr", has_text=newinv["invoiceNumber"]).locator("[data-edit]").click(); pg.wait_for_timeout(200)
    rows = pg.locator("#lineItemsBody tr")
    for i in range(rows.count()):
        if "0009" in rows.nth(i).inner_text(): rows.nth(i).locator("[data-remove]").click(); break
    pg.wait_for_timeout(80); print("note after removing:", pg.inner_text("#invSourceOrderNote"))
    pg.click("#saveInvoiceBtn"); pg.wait_for_timeout(150)
    print("after removal:", O(pg))
    # legacy invoice edit/save keeps i3 invoiced
    pg.click("button[data-tab='invoices']"); pg.wait_for_timeout(100)
    pg.locator("#invoiceListWrap tr", has_text="INV-PCC-2026-1003").locator("[data-edit]").click(); pg.wait_for_timeout(200)
    print("legacy note:", pg.inner_text("#invSourceOrderNote"))
    pg.click("#saveInvoiceBtn"); pg.wait_for_timeout(150)
    print("i3 still invoiced:", O(pg)["ORD-PCC-2026-0007"]["i3"])
    # delete multi-order invoice releases all its items
    pg.click("button[data-tab='invoices']"); pg.wait_for_timeout(100)
    b.close()
print("ERRORS:", errs)
