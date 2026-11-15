from playwright.sync_api import sync_playwright
exec(open('test_n.py').read().split('\nerrs=[]\n')[0])
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    for vw,vh,name in [(1366,860,"o_desktop"),(820,1000,"o_tablet"),(390,844,"o_phone")]:
        pg = b.new_page(viewport={"width":vw,"height":vh})
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(html)
        pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify([d.cust])); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_settings_v1', JSON.stringify({nextOrderNum:10, invPrefix:'PCC', nextInvNum:1004, machineRate:0.3, laborRate:20, targetMargin:50})); }""", {"catalog":catalog,"cust":cust,"orders":orders,"mats":mats})
        pg.reload(); pg.wait_for_timeout(300)
        pg.click("button[data-tab='orders']"); pg.wait_for_timeout(200)
        pg.screenshot(path=name+".png")
        if name=="o_desktop":
            pg.locator("#orderListWrap tr", has_text="ORD-PCC-2026-0007").locator("[data-oedit]").click(); pg.wait_for_timeout(250)
            pg.mouse.wheel(0,600); pg.wait_for_timeout(200)
            pg.screenshot(path="o_desktop_order.png")
            pg.click("[data-oselect='i1']"); pg.click("#createInvFromOrderBtn"); pg.wait_for_timeout(300)
            print("active on editor:", pg.eval_on_selector("nav.tabs button.active","e=>e.dataset.tab"))
        pg.close()
    b.close()
print("ERRORS:", errs)
