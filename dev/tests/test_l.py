from playwright.sync_api import sync_playwright
import json
exec(open('test_k.py').read().split('\nerrs=[]\n')[0])
orders[2]["name"]="Guild retreat, trays"   # name with a comma
errs=[]
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
    pg.click("#addFromOrdersBtn"); pg.wait_for_timeout(100); pg.click("#afoList [data-afoall='o3']"); pg.click("#afoAdd"); pg.wait_for_timeout(150)
    print("event field:", pg.input_value("#invEvent"))
    pg.click("#previewBtn")
    pg.wait_for_timeout(200)
    lines = pg.eval_on_selector("#pInvEvent","e=>[...e.childNodes].map(n=>n.textContent)")
    print("printed event parts:", lines)
    print("rendered:", pg.inner_text("#pInvEventRow").replace("\n"," ⏎ "))
    print("style inside print area:", "p-ev-line" in pg.eval_on_selector("#printArea","e=>e.innerHTML") and "<style>" in pg.eval_on_selector("#printArea","e=>e.innerHTML"))
    pg.screenshot(path="l_print.png", clip={"x":240,"y":20,"width":800,"height":320})
    pg.evaluate("document.getElementById('closePreviewBtn').click()"); pg.wait_for_timeout(80)
    # single order event unchanged
    pg.fill("#invEvent","Order ORD-PCC-2026-0007 · Holiday craft fair batch")
    pg.click("#previewBtn"); pg.wait_for_timeout(150)
    print("single:", pg.inner_text("#pInvEventRow").replace("\n"," ⏎ "))
    pg.evaluate("document.getElementById('closePreviewBtn').click()"); pg.wait_for_timeout(80)
    # custom text unchanged
    pg.fill("#invEvent","Fall Craft Fair 2026, booth 12")
    pg.click("#previewBtn"); pg.wait_for_timeout(150)
    print("custom:", pg.inner_text("#pInvEventRow").replace("\n"," ⏎ "))
    b.close()
print("ERRORS:", errs)
