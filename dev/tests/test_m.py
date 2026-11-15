from playwright.sync_api import sync_playwright
import json
exec(open('test_k.py').read().split('\nerrs=[]\n')[0])
orders[2]["items"][0]["notes"]="Logo on side wall"
# an older linked invoice (lines have order links but no notes key) covering i2 (notes empty) — give i2 a note
orders[0]["items"][1]["notes"]="Gift boxed"; orders[0]["items"][1]["completedDate"]="2026-11-10"; orders[0]["items"][1]["invoiceId"]="inv2"
inv.append({"id":"inv2","invoiceNumber":"INV-PCC-2026-1002","date":"2026-11-10","dueDate":"","status":"sent","event":"","customerId":"c1","customer":customers[0],
  "lineItems":[{"productId":"p2","orderId":"o1","orderItemId":"i2","orderNumber":"ORD-PCC-2026-0007","name":"Business Card Holder","part":"PCC-BCH-02","custPart":"","qty":4,"price":18,"extended":72}],
  "sourceOrderIds":["o1"],"sourceOrderId":"o1","taxable":True,"taxRate":7,"subtotal":72,"taxAmount":5.04,"total":77.04,"notes":""})
errs=[]
def printed(pg, num):
    pg.click("button[data-tab='invoices']"); pg.wait_for_timeout(100)
    pg.locator("#invoiceListWrap tr", has_text=num).locator("[data-print]").click(); pg.wait_for_timeout(200)
    r = pg.eval_on_selector_all("#pLineItems tr","rs=>rs.map(r=>r.children[0].innerText.replace(/\\n/g,' / '))")
    pg.evaluate("document.getElementById('closePreviewBtn').click()"); pg.wait_for_timeout(80)
    return r
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1280,"height":900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify(d.customers)); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); localStorage.setItem('pcc_invoices_v1', JSON.stringify(d.inv)); localStorage.setItem('pcc_settings_v1', JSON.stringify({nextOrderNum:10, invPrefix:'PCC', nextInvNum:1004})); }""", {"catalog":catalog,"customers":customers,"orders":orders,"inv":inv})
    pg.reload(); pg.wait_for_timeout(300)
    print("older invoice print:", printed(pg, "INV-PCC-2026-1002"))
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.locator("#orderListWrap tr", has_text="ORD-PCC-2026-0007").locator("[data-oedit]").click(); pg.wait_for_timeout(250)
    pg.click("[data-oselect='i1']"); pg.click("#createInvFromOrderBtn"); pg.wait_for_timeout(300)
    pg.click("#addFromOrdersBtn"); pg.wait_for_timeout(100); pg.click("#afoList [data-afoall='o3']"); pg.click("#afoAdd"); pg.wait_for_timeout(150)
    print("editor notes:", pg.eval_on_selector_all("#lineItemsBody .inv-note-input","e=>e.map(x=>x.value)"))
    pg.locator("#lineItemsBody .inv-note-input").nth(1).fill("Logo on side wall — per proof v2")
    pg.screenshot(path="m_editor.png", clip={"x":100,"y":0,"width":1080,"height":900}, full_page=True)
    pg.click("#saveInvoiceBtn"); pg.wait_for_timeout(150)
    saved = [i for i in json.loads(pg.evaluate("localStorage.getItem('pcc_invoices_v1')")) if i["invoiceNumber"]=="INV-PCC-2026-1004"][0]
    print("saved notes:", [l.get("notes") for l in saved["lineItems"]])
    print("print:", printed(pg, "INV-PCC-2026-1004"))
    # clearing a note removes it from print
    pg.locator("#invoiceListWrap tr", has_text="INV-PCC-2026-1004").locator("[data-edit]").click(); pg.wait_for_timeout(200)
    pg.locator("#lineItemsBody .inv-note-input").nth(0).fill(""); pg.click("#saveInvoiceBtn"); pg.wait_for_timeout(150)
    print("after clearing:", printed(pg, "INV-PCC-2026-1004"))
    pg.locator("#invoiceListWrap tr", has_text="INV-PCC-2026-1004").locator("[data-print]").click(); pg.wait_for_timeout(200)
    pg.screenshot(path="m_print.png")
    b.close()
print("ERRORS:", errs)
