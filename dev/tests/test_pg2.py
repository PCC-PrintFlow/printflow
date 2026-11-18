from playwright.sync_api import sync_playwright
exec(open('test_n.py').read().split('\nerrs=[]\n')[0])
catalog[0]["makesPurge"]=True; catalog[0]["purgePerBlock"]=20
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1366,"height":1000})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_settings_v1', JSON.stringify({machineRate:0.3, laborRate:20, targetMargin:50})); }""", {"catalog":catalog,"mats":mats})
    pg.reload(); pg.wait_for_timeout(300)
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(150)
    for part in ["PCC-KIT","PCC-KC-01","PCC-ST"]:
        row = pg.locator("#catalogListWrap tbody tr", has_text=part).first
        print(part, "| cost:", row.locator("td").nth(3).inner_text().replace("\n"," "), "| margin:", row.locator("td").nth(5).inner_text().replace("\n"," "))
    pg.screenshot(path="pg2_cat.png", clip={"x":248,"y":250,"width":1118,"height":330})
    pg.evaluate("document.querySelectorAll('[data-kittoggle]').forEach(function(b){ if(b.getAttribute('aria-expanded')!=='true') b.click(); })")  # kits start collapsed
    pg.locator("#catalogListWrap [data-editprod='p1']").first.click(); pg.wait_for_timeout(150)
    print("editor:", pg.inner_text("#pmSummary").replace("\n"," | "))
    pg.click("#pmCancel")
    pg.locator("#catalogListWrap [data-editprod='p4']").first.click(); pg.wait_for_timeout(150)
    print("kit editor:", pg.inner_text("#pmSummary").replace("\n"," | ")[-160:])
    b.close()
print("ERRORS:", errs)
