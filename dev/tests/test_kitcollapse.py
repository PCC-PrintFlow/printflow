from playwright.sync_api import sync_playwright
import json
exec(open('test_n.py').read().split('\nerrs=[]\n')[0])
catalog.append({"id":"p5","name":"Craft Fair Bundle","part":"PCC-BUN","custPart":"","price":20,"isKit":True,"kitItems":[{"productId":"p1","qty":3},{"productId":"p2","qty":2}],"bom":[],"printHours":0,"laborMin":0,"extraCost":0})
errs=[]
def hidden_members(pg):
    return pg.eval_on_selector_all("#catalogListWrap tr[data-kitparent]","rs=>rs.map(r=>[r.dataset.kitparent, r.hidden, r.offsetParent!==null])")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1366,"height":900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify([d.cust])); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_settings_v1', JSON.stringify({nextOrderNum:10, invPrefix:'PCC', nextInvNum:1004, machineRate:0.3, laborRate:20, targetMargin:50})); }""", {"catalog":catalog,"cust":cust,"orders":orders,"mats":mats})
    pg.reload(); pg.wait_for_timeout(300)
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(200)
    print("tab rows:", pg.eval_on_selector_all("#catalogListWrap tbody tr","rs=>rs.slice(0,6).map(r=>r.className+': '+r.children[0].innerText.replace(/\\n/g,' / '))"))
    rows = hidden_members(pg)
    print("members on load:", rows)
    assert rows and all(r[1] and not r[2] for r in rows), "kit members should start collapsed"
    toggles = pg.locator("[data-kittoggle]")
    print("toggles:", toggles.count(), [toggles.nth(i).get_attribute("aria-expanded") for i in range(toggles.count())])
    first = toggles.first; kid = first.get_attribute("data-kittoggle")
    first.click(); pg.wait_for_timeout(100)
    rows = hidden_members(pg)
    assert all((not r[1] and r[2]) == (r[0]==kid) for r in rows), rows
    assert first.get_attribute("aria-expanded") == "true"
    # stays open after a re-render
    pg.click("#catSwFair"); pg.wait_for_timeout(100); pg.click("#catSwMain"); pg.wait_for_timeout(150)
    assert any(r[0]==kid and r[2] for r in hidden_members(pg)), "expanded state lost on re-render"
    pg.locator("[data-kittoggle='%s']"%kid).click(); pg.wait_for_timeout(100)
    assert all(r[1] for r in hidden_members(pg)), "collapse again failed"
    print("kit collapse OK")
    b.close()
print("ERRORS:", errs)
