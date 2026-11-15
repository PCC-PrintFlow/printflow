from playwright.sync_api import sync_playwright
exec(open('snap.py').read().split("with sync_playwright()")[0])  # reuse sample data
items[1]["needByDate"]="2026-11-14"
items[2]["completedDate"]="2026-11-06"; items[2]["invoiceId"]="inv1"; items[2]["invoicedAt"]="2026-11-07"
invoices=[{"id":"inv1","invoiceNumber":"INV-PCC-2026-1003","date":"2026-11-07","dueDate":"2026-12-07","status":"sent","event":"Order ORD-PCC-2026-0007","customerId":"c1","customer":customers[0],"lineItems":[{"name":"Fabric Stack Tray 8x8","part":"PCC-FT-08","custPart":"ACM-9910","qty":10,"price":14,"extended":140}],"taxable":True,"taxRate":7,"subtotal":140,"taxAmount":9.8,"total":149.8,"notes":""}]
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1280,"height":900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify(d.customers)); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); localStorage.setItem('pcc_invoices_v1', JSON.stringify(d.invoices)); }""", {"catalog":catalog,"customers":customers,"orders":orders,"invoices":invoices})
    pg.reload()
    pg.screenshot(path="a_blank.png", full_page=True)
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(200)
    pg.locator("#orderListWrap button", has_text="Edit").first.click(); pg.wait_for_timeout(300)
    # select item 1 for invoice
    pg.click("[data-oselect='i1']"); pg.wait_for_timeout(150)
    pg.screenshot(path="a_loaded.png", full_page=True)
    print("bar:", pg.inner_text("#createInvFromOrderBtn"), "| disabled:", pg.is_disabled("#createInvFromOrderBtn"))
    # set completed date on item 2 -> invoice button should enable
    pg.fill("#oi-completedDate-i2", "2026-11-10"); pg.wait_for_timeout(150)
    print("item2 side:", pg.inner_text("[data-side-for='i2']").replace("\n"," | "))
    print("progress:", pg.inner_text("#orderProgress").replace("\n"," | "))
    # change base color -> dot
    pg.fill("#oi-baseColor-i2", "Matte Blue"); print("dot style:", pg.get_attribute("[data-card-for='i2'] .of-dot", "style"))
    # expand invoiced item
    pg.click("[data-oexpand='i3']"); pg.wait_for_timeout(150)
    print("i3 expanded has product select:", pg.locator("#oi-product-i3").count())
    # customer: edit / done / change
    pg.click("#ordEditCustBtn"); print("form visible after edit:", pg.is_visible("#ordCustFormPanel"), pg.is_visible("#ordCustSummary"))
    pg.click("#ordCustDoneBtn"); print("summary after done:", pg.is_visible("#ordCustSummary"))
    # create invoice
    pg.click("#createInvFromOrderBtn"); pg.wait_for_timeout(300)
    rows = pg.locator("#lineItemsBody tr").count(); print("invoice draft lines:", rows)
    # new blank
    pg.click("button[data-tab='neworder']"); pg.wait_for_timeout(200)
    pg.click("#resetOrderFormBtn"); pg.wait_for_timeout(200)
    btn = pg.locator("#confirmOk, .modal button.btn:not(.secondary)").first
    if btn.count(): btn.click(); pg.wait_for_timeout(200)
    print("blank: form visible", pg.is_visible("#ordCustFormPanel"), "| cards", pg.locator(".of-card").count(), "| pill", pg.inner_text("#orderStatusPill"))
    pg.set_viewport_size({"width":420,"height":900}); pg.wait_for_timeout(200)
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(200)
    pg.locator("#orderListWrap button", has_text="Edit").first.click(); pg.wait_for_timeout(300)
    pg.screenshot(path="a_mobile.png", full_page=True)
    b.close()
print("ERRORS:", errs)
