from playwright.sync_api import sync_playwright
import json, os
exec(open('test_n.py').read().split('\nerrs=[]\n')[0])
# Craft Fair Catalog items: keychain (p1) and a dragon (p5); the sticker (p2) is business-only
catalog[0]["catalog"] = "fair"
catalog.append({"id":"p5","name":"Dragon","part":"SB-DR1","custPart":"","price":10,"catalog":"fair","bom":[{"materialId":"m1","qty":20}],"printHours":1,"laborMin":0,"extraCost":0})
errs = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1280,"height":1000})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_customers_v1', JSON.stringify([d.cust])); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); }""",
                {"catalog":catalog,"mats":mats,"cust":cust,"orders":orders})
    pg.reload(); pg.wait_for_timeout(300)
    pg.click("button[data-tab='neworder']"); pg.wait_for_timeout(150)

    # customer order is unchanged: customer panel visible, no catalog/custom buttons
    assert pg.is_visible("#ordCustFormPanel"), "customer form should show for a customer order"
    assert pg.is_hidden("#ordFromCatalogBtn") and pg.is_hidden("#ordCustomReqBtn")
    assert pg.is_visible("#createInvFromOrderBtn")

    # switch to replenishment
    pg.click("[data-okind='replenish']"); pg.wait_for_timeout(100)
    assert pg.is_hidden("#ordCustFormPanel") and pg.is_hidden("#ordCustSummary")
    assert pg.is_visible("#ordFromCatalogBtn") and pg.is_visible("#ordCustomReqBtn")
    assert pg.is_hidden("#createInvFromOrderBtn")
    pg.fill("#orderName", "Holiday fair restock")

    # catalog picker: Craft Fair items only, until the box is ticked
    pg.click("#ordFromCatalogBtn"); pg.wait_for_timeout(100)
    names = pg.eval_on_selector_all("#ordPickerList .nm", "e=>e.map(x=>x.textContent.trim())")
    print("picker (fair only):", names)
    assert names == ["Dragon", "Keychain"], names
    pg.check("#ordPickerAll"); pg.wait_for_timeout(80)
    names2 = pg.eval_on_selector_all("#ordPickerList .nm", "e=>e.map(x=>x.textContent.trim())")
    print("picker (all):", names2)
    assert "Sticker" in names2 and any(n.startswith("Keychain Gift Kit") for n in names2)
    pg.uncheck("#ordPickerAll")
    pg.fill("#ordpk-p1", "12"); pg.fill("#ordpk-p5", "6")
    assert "2 items · 18 pieces" in pg.inner_text("#ordPickerSummary"), pg.inner_text("#ordPickerSummary")
    pg.click("#ordPickerAdd"); pg.wait_for_timeout(120)
    assert pg.is_hidden("#ordPicker")
    cards = pg.eval_on_selector_all(".of-card", "e=>e.length"); print("cards after picker:", cards)
    assert cards == 2, "the lone blank row should be replaced, not kept"
    assert "2 items · 18 pieces" in pg.inner_text("#orderItemCount")

    # adding the same product again just bumps the existing line
    pg.click("#ordFromCatalogBtn"); pg.fill("#ordpk-p1", "3"); pg.click("#ordPickerAdd"); pg.wait_for_timeout(100)
    assert pg.eval_on_selector_all(".of-card", "e=>e.length") == 2
    assert pg.input_value("#oi-qty-" + pg.eval_on_selector(".of-card", "e=>e.dataset.cardFor")) in ("15", "6")  # keychain 12+3 (or dragon 6, whichever card is first)

    # custom request
    pg.click("#ordCustomReqBtn"); pg.wait_for_timeout(100)
    cid = pg.eval_on_selector_all(".of-card", "e=>e[e.length-1].dataset.cardFor")
    pg.fill("#oi-name-" + cid, "Glow-in-the-dark dragon keychains")
    pg.fill("#oi-qty-" + cid, "8")
    pg.fill("#oi-notes-" + cid, "Teal body, gold eyes")
    assert "Custom request" in pg.inner_text("[data-meta-for='%s']" % cid)
    side = pg.inner_text("[data-side-for='%s']" % cid)
    assert "Invoice this item" not in side and "Move to another order" not in side and "Remove item" in side, side
    pg.screenshot(path="replenish_form.png", full_page=True)

    # save: no customer needed
    pg.click("#saveOrderBtn"); pg.wait_for_timeout(150)
    saved = json.loads(pg.evaluate("localStorage.getItem('pcc_orders_v1')"))
    so = [o for o in saved if o.get("kind") == "replenish"]
    assert len(so) == 1 and len(saved) == 2, "one new replenishment order saved next to the old order"
    so = so[0]
    print("saved:", so["orderNumber"], so["name"], so["customer"]["name"], [(i["name"], i["qty"], i.get("custom")) for i in so["items"]])
    assert so["customer"]["name"] == "Craft fair stock" and so["customerId"] is None
    assert [i["productId"] for i in so["items"]] == ["p1", "p5", ""]
    assert [bool(i.get("custom")) for i in so["items"]] == [False, False, True]
    assert so["items"][2]["name"] == "Glow-in-the-dark dragon keychains" and so["items"][2]["qty"] == 8
    # the existing customer order is untouched, and has no new fields
    old = [o for o in saved if o["id"] == "o1"][0]
    assert "kind" not in old and all("custom" not in i for i in old["items"])

    # order history: stock order is labelled, not "invoiced"
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(120)
    row = pg.locator("#orderListWrap tr", has_text=so["orderNumber"]).inner_text().replace("\n", " | ")
    print("list row:", row)
    assert "Craft fair restock" in row and "Stock order" in row and "Craft fair stock" not in row.replace("restock", "")

    # reload: kind and custom flag persist; customer fields stay blank
    pg.reload(); pg.wait_for_timeout(250)
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(120)
    pg.locator("#orderListWrap tr", has_text=so["orderNumber"]).locator("[data-oedit]").click(); pg.wait_for_timeout(200)
    assert pg.is_hidden("#ordCustFormPanel") and pg.is_visible("#ordCustomReqBtn")
    assert pg.input_value("#ordCustName") == ""
    assert pg.eval_on_selector_all(".of-card", "e=>e.length") == 3
    assert pg.input_value("#oi-name-" + so["items"][2]["id"]) == "Glow-in-the-dark dragon keychains"

    # a replenishment item never shows up as "ready to invoice"
    pg.click("[data-okind='customer']"); pg.wait_for_timeout(100)
    assert pg.is_visible("#confirmModal"), "switching back to a customer order should warn about the custom request"
    assert "custom request" in pg.inner_text("#confirmText")
    pg.click("#confirmCancel"); pg.wait_for_timeout(80)
    assert pg.is_visible("#ordCustomReqBtn"), "cancel keeps the replenishment order"
    # mark an item Done: still no invoice buttons, no invoice bar
    pg.select_option("#oi-status-" + so["items"][0]["id"], "done"); pg.wait_for_timeout(100)
    assert "Invoice this item" not in pg.inner_text("[data-side-for='%s']" % so["items"][0]["id"])
    assert "items made" in pg.inner_text("#orderProgress")
    pg.click("#saveOrderBtn"); pg.wait_for_timeout(100)
    # the invoice editor's "add items from other orders" list must not offer the stock order's Done item
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.locator("#orderListWrap tr", has_text="ORD-PCC-2026-0007").locator("[data-oedit]").click(); pg.wait_for_timeout(250)
    pg.click("[data-oselect='i1']"); pg.click("#createInvFromOrderBtn"); pg.wait_for_timeout(300)
    pg.click("#addFromOrdersBtn"); pg.wait_for_timeout(100)
    pg.check("#afoAllCust"); pg.wait_for_timeout(100)
    modal = pg.inner_text("#afoModal")
    print("afo modal:", modal.replace("\n", " | ")[:200])
    assert so["orderNumber"] not in modal, "replenishment order must not be offered for invoicing"
    pg.click("#afoCancel"); pg.wait_for_timeout(80)

    # printable order form + PDF doc describe it as stock
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.locator("#orderListWrap tr", has_text=so["orderNumber"]).locator("[data-oview]").click(); pg.wait_for_timeout(200)
    pa = pg.inner_text("#orderPrintArea")
    print("print:", pa.replace("\n", " | ")[:300])
    assert "own stock" in pa and "(custom request)" in pa
    pg.evaluate("document.getElementById('closePreviewBtn').click()"); pg.wait_for_timeout(80)

    # start a new blank form: back to a customer order
    pg.click("button[data-tab='neworder']"); pg.wait_for_timeout(80)
    pg.click("#resetOrderFormBtn"); pg.wait_for_timeout(150)
    if pg.is_visible("#confirmModal"): pg.click("#confirmOk"); pg.wait_for_timeout(100)
    assert pg.is_visible("#ordCustFormPanel") and pg.is_hidden("#ordCustomReqBtn") and pg.is_visible("#createInvFromOrderBtn")
    print("OK")
print("ERRORS:", errs)
