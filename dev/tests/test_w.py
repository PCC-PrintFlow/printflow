from playwright.sync_api import sync_playwright
import json
exec(open('test_n.py').read().split('\nerrs=[]\n')[0])
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1366,"height":1100})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify([d.cust])); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_settings_v1', JSON.stringify({nextOrderNum:10, invPrefix:'PCC', nextInvNum:1005, machineRate:0.3, laborRate:20, targetMargin:50})); }""", {"catalog":catalog,"cust":cust,"orders":orders,"mats":mats})
    pg.reload(); pg.wait_for_timeout(300)
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(150)
    pg.evaluate("document.querySelectorAll('[data-kittoggle]').forEach(function(b){ if(b.getAttribute('aria-expanded')!=='true') b.click(); })")  # kits start collapsed
    pg.locator("#catalogListWrap [data-editprod='p1']").first.click(); pg.wait_for_timeout(150)
    print("before:", pg.inner_text("#pmSummary").replace("\n"," | ")[:160])
    # whole plate: 12 keychains, 144 g, 6 h
    pg.fill("#pmPerPrint","12"); pg.dispatch_event("#pmPerPrint","input"); pg.wait_for_timeout(80)
    pg.locator('[data-bm="qty"]').first.fill("144"); pg.locator('[data-bm="qty"]').first.dispatch_event("input")
    pg.fill("#pmHours","6"); pg.dispatch_event("#pmHours","input"); pg.wait_for_timeout(100)
    print("labels:", pg.inner_text("#pmBomTitle"), "|", pg.inner_text("#pmHoursLabel"), "|", pg.inner_text("#pmBom thead th:nth-child(2)"))
    print("summary:", pg.inner_text("#pmSummary").replace("\n"," | "))
    pg.locator("#pmBatchBox").scroll_into_view_if_needed()
    pg.screenshot(path="w_editor.png")
    pg.click("#pmSave"); pg.wait_for_timeout(150)
    row = pg.locator("#catalogListWrap tbody tr", has_text="PCC-KC-01").first
    print("catalog:", row.locator("td").nth(3).inner_text(), row.locator("td").nth(5).inner_text())
    st=json.loads(pg.evaluate("localStorage.getItem('pcc_catalog_v1')"))
    print("stored:", [(x["id"],x.get("perPrint"),x["bom"][0]["qty"],x["printHours"]) for x in st if x["id"]=="p1"])
    pg.locator("#catalogListWrap [data-editprod='p4']").first.click(); pg.wait_for_timeout(150)
    print("kit batch box visible:", pg.is_visible("#pmBatchBox"))
    b.close()
print("ERRORS:", errs)
