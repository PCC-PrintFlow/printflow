from playwright.sync_api import sync_playwright
exec(open('test_n.py').read().split('\nerrs=[]\n')[0])
# add materials whose names sort before "PLA Basic"
mats.insert(0, {"id":"m0","name":"ABS","type":"filament","unit":"g","packPrice":21,"packQty":1000,"notes":""})
mats.append({"id":"m5","name":"pla basic","type":"filament","unit":"g","packPrice":19.99,"packQty":1000,"notes":"dup lower"})  # not used; m1 'PLA Basic' should win (first exact A-Z)
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1366,"height":1000})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_settings_v1', JSON.stringify({machineRate:0.3, laborRate:20, targetMargin:50})); }""", {"catalog":catalog,"mats":mats})
    pg.reload(); pg.wait_for_timeout(300)
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(150)
    pg.fill("#catName","Test item"); pg.click("#catAddBtn"); pg.wait_for_timeout(150)
    sel = lambda: pg.eval_on_selector_all('#pmBom select','e=>e.map(s=>s.options[s.selectedIndex].text)')
    print("new product BOM:", sel())
    pg.click("#pmAddLine"); pg.wait_for_timeout(80)
    print("after add line:", sel())
    pg.click("#pmCancel")
    # product with no BOM -> add line defaults to PLA Basic
    pg.locator("#catalogListWrap [data-editprod='p2']").first.click(); pg.wait_for_timeout(150)
    pg.click("#pmAddLine"); pg.wait_for_timeout(80)
    print("empty product add line:", sel())
    b.close()
print("ERRORS:", errs)
