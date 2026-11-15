from playwright.sync_api import sync_playwright
import json
exec(open('test_j.py').read().split('\nerrs=[]\n')[0])
orders[0]["name"]="Holiday craft fair batch"
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
    # A) single invoice from named order
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.locator("#orderListWrap tr", has_text="ORD-PCC-2026-0007").locator("[data-oedit]").click(); pg.wait_for_timeout(250)
    pg.click("[data-oselect='i1']"); pg.click("#createInvFromOrderBtn"); pg.wait_for_timeout(300)
    print("A editor note:", pg.eval_on_selector_all("#lineItemsBody .inv-from","e=>e.map(x=>x.innerText)"))
    # B) add unnamed order item -> multi-order
    pg.click("#addFromOrdersBtn"); pg.wait_for_timeout(100); pg.click("#afoList [data-afoall='o3']"); pg.click("#afoAdd"); pg.wait_for_timeout(150)
    print("B editor notes:", pg.eval_on_selector_all("#lineItemsBody .inv-from","e=>e.map(x=>x.innerText)"))
    pg.click("#saveInvoiceBtn"); pg.wait_for_timeout(150)
    print("B saved line orderName:", [l.get("orderName") for l in json.loads(pg.evaluate("localStorage.getItem('pcc_invoices_v1')"))[-1]["lineItems"]])
    print("B printed:", printed(pg, "INV-PCC-2026-1004"))
    # C) single invoice from unnamed order (o2, other customer)
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.locator("#orderListWrap tr", has_text="ORD-PCC-2026-0008").locator("[data-oedit]").click(); pg.wait_for_timeout(250)
    pg.click("[data-oselect='j1']"); pg.click("#createInvFromOrderBtn"); pg.wait_for_timeout(300); pg.click("#saveInvoiceBtn"); pg.wait_for_timeout(150)
    print("C printed (unnamed single):", printed(pg, "INV-PCC-2026-1005"))
    # D) rename order 0009 -> existing invoice print picks it up
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.locator("#orderListWrap tr", has_text="ORD-PCC-2026-0009").locator("[data-oedit]").click(); pg.wait_for_timeout(250)
    pg.fill("#orderName","Guild retreat trays"); pg.click("#saveOrderBtn"); pg.wait_for_timeout(100)
    print("D printed after rename:", printed(pg, "INV-PCC-2026-1004"))
    pg.click("button[data-tab='invoices']"); pg.wait_for_timeout(100)
    pg.locator("#invoiceListWrap tr", has_text="INV-PCC-2026-1004").locator("[data-print]").click(); pg.wait_for_timeout(200)
    pg.screenshot(path="k_print.png")
    b.close()
print("ERRORS:", errs)
