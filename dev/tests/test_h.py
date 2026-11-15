from playwright.sync_api import sync_playwright
import json
exec(open('test_g.py').read().split("errs=[]")[0])   # same fixtures as test_g
errs=[]
def order(pg,num): return [o for o in json.loads(pg.evaluate("localStorage.getItem('pcc_orders_v1')")) if o["orderNumber"]==num]
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
    print("i2 options:", pg.eval_on_selector("#oi-status-i2","e=>[...e.options].map(o=>o.text)"))
    print("invoiced i3 options:", pg.eval_on_selector("#oi-status-i3","e=>[...e.options].map(o=>o.text)"))
    # Delivered on a not-done item -> fills completed + delivered, shows Delivered date field, invoicable
    pg.select_option("#oi-status-i2","delivered"); pg.wait_for_timeout(100)
    print("i2 delivered:", pg.eval_on_selector("#oi-status-i2","e=>e.options[e.selectedIndex].text"), "| completed:", pg.input_value("#oi-completedDate-i2"), "| delivered field:", pg.input_value("#oi-deliveredDate-i2"), "| invoice btn:", pg.locator("[data-oselect='i2']").count())
    # back to Done clears delivered
    pg.select_option("#oi-status-i2","done"); pg.wait_for_timeout(80)
    print("i2 done:", pg.eval_on_selector("#oi-status-i2","e=>e.options[e.selectedIndex].text"), "| delivered field present:", pg.locator("#oi-deliveredDate-i2").count())
    pg.select_option("#oi-status-i2","delivered"); pg.wait_for_timeout(80)
    pg.fill("#oi-completedDate-i2",""); pg.wait_for_timeout(100)
    print("clearing completed ->", pg.eval_on_selector("#oi-status-i2","e=>e.options[e.selectedIndex].text"), "| delivered field present:", pg.locator("#oi-deliveredDate-i2").count())
    # invoiced item -> delivered
    pg.select_option("#oi-status-i3","delivered"); pg.wait_for_timeout(100)
    print("invoiced i3:", pg.eval_on_selector("#oi-status-i3","e=>e.options[e.selectedIndex].text"), "| card text:", pg.inner_text("[data-card-for='i3'] .of-meta"))
    pg.click("#saveOrderBtn"); pg.wait_for_timeout(100)
    o = order(pg,"ORD-PCC-2026-0007")[0]
    print("saved:", [(i["id"], i.get("completedDate"), i.get("deliveredDate")) for i in o["items"]])
    # grouped view has Delivered group
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.click("[data-olmode='group']"); pg.check("#orderShowInvoiced"); pg.wait_for_timeout(100)
    print("groups:", pg.eval_on_selector_all(".ofg-head","hs=>hs.map(h=>h.innerText.replace(/\\n/g,' '))"))
    pg.click("[data-olmode='orders']"); pg.uncheck("#orderShowInvoiced") if pg.is_visible("#orderShowInvoiced") else None
    # partial move: i1 qty 25 -> move 10 to new order
    pg.locator("#orderListWrap tr", has_text="ORD-PCC-2026-0007").locator("[data-oedit]").click(); pg.wait_for_timeout(250)
    pg.click("[data-omove='i1']"); pg.wait_for_timeout(100)
    print("qty box:", pg.is_visible("#mvQtyWrap"), pg.input_value("#mvQty"), "of", pg.inner_text("#mvQtyOf"), "| btn:", pg.inner_text("#mvConfirm"))
    pg.fill("#mvQty","10"); pg.wait_for_timeout(50); print("btn now:", pg.inner_text("#mvConfirm"))
    pg.screenshot(path="h_partial.png")
    pg.click("#mvConfirm"); pg.wait_for_timeout(250)
    print("toast:", pg.inner_text("#toast"))
    src = order(pg,"ORD-PCC-2026-0007")[0]; new = order(pg,"ORD-PCC-2026-0010")[0]
    print("source items:", [(i["id"], i["name"][:12], i["qty"]) for i in src["items"]])
    print("new order items:", [(i["id"]!="i1", i["name"][:12], i["qty"], i["baseColor"]) for i in new["items"]])
    # partial of only item: o3 k1 qty 5, move 2 -> delete-source hidden; then move all 3 -> shown
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.locator("#orderListWrap tr", has_text="ORD-PCC-2026-0009").locator("[data-oedit]").click(); pg.wait_for_timeout(250)
    pg.click("[data-omove='k1']"); pg.wait_for_timeout(100)
    print("only item full qty -> delete shown:", pg.is_visible("#mvDeleteSourceWrap"))
    pg.fill("#mvQty","2"); pg.wait_for_timeout(50); print("partial -> delete shown:", pg.is_visible("#mvDeleteSourceWrap"))
    pg.check("#mvDestExisting"); pg.locator("#mvOrderList input[value='o1']").check(); pg.click("#mvConfirm"); pg.wait_for_timeout(250)
    print("toast:", pg.inner_text("#toast"))
    print("0009:", [(i["qty"]) for i in order(pg,"ORD-PCC-2026-0009")[0]["items"]], "| 0007 items:", [(i["name"][:10], i["qty"]) for i in order(pg,"ORD-PCC-2026-0007")[0]["items"]])
    # invalid qty
    pg.click("[data-omove='k1']"); pg.wait_for_timeout(100); pg.fill("#mvQty","0"); pg.click("#mvConfirm"); pg.wait_for_timeout(80)
    print("zero qty toast:", pg.inner_text("#toast"), "| modal still open:", pg.is_visible("#moveItemModal"))
    pg.click("#mvCancel")
    # print view status column
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.locator("#orderListWrap tr", has_text="ORD-PCC-2026-0007").locator("[data-oview]").click(); pg.wait_for_timeout(200)
    print("print status:", pg.eval_on_selector_all("#oItems tr","rs=>rs.map(r=>r.children[7].innerText)"))
    b.close()
print("ERRORS:", errs)
