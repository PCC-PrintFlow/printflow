from playwright.sync_api import sync_playwright
import json
exec(open('test_n.py').read().split('\nerrs=[]\n')[0])
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1366,"height":1000})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify([d.cust])); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_settings_v1', JSON.stringify({nextOrderNum:10, invPrefix:'PCC', nextInvNum:1004, machineRate:0.3, laborRate:20, targetMargin:50})); }""", {"catalog":catalog,"cust":cust,"orders":orders,"mats":mats})
    pg.reload(); pg.wait_for_timeout(300)
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(200)
    cat = lambda: json.loads(pg.evaluate("localStorage.getItem('pcc_catalog_v1')"))
    # 1) filament details + printer dropdown on an existing product
    pg.evaluate("document.querySelectorAll('[data-kittoggle]').forEach(b=>b.click())")
    pg.locator("[data-editprod='p1']").first.click(); pg.wait_for_timeout(200)
    opts = pg.eval_on_selector_all("select[data-bx='printer'] option","o=>o.map(x=>x.textContent)")
    print("printer options:", opts)
    assert opts[1:]==["Bambu H2D","Bambu X1C","Bambu P1S","Bambu A2L","Sovol SV06","Prusa MK3S+"], opts
    pg.locator("input[data-bx='brand']").first.fill("Bambu Lab")
    pg.locator("input[data-bx='color']").first.fill("Jade White")
    pg.locator("input[data-bx='ftype']").first.fill("PLA")
    pg.locator("select[data-bx='printer']").first.select_option("Bambu P1S")
    pg.click("#pmSave"); pg.wait_for_timeout(200)
    line = [x for x in cat() if x["id"]=="p1"][0]["bom"][0]
    print("saved line:", line)
    assert (line["brand"],line["color"],line["ftype"],line["printer"])==("Bambu Lab","Jade White","PLA","Bambu P1S")
    # reopen -> values restored
    pg.locator("[data-editprod='p1']").first.click(); pg.wait_for_timeout(200)
    assert pg.input_value("input[data-bx='brand']")=="Bambu Lab" and pg.input_value("select[data-bx='printer']")=="Bambu P1S"
    pg.click("#pmCancel"); pg.wait_for_timeout(100)
    # 2) new product with "also add to a kit"
    pg.fill("#catName","Fridge Magnet"); pg.fill("#catPrice","3"); pg.click("#catAddBtn"); pg.wait_for_timeout(250)
    assert pg.is_visible("#pmAddToKitRow")
    pg.select_option("#pmAddToKit", "p4"); pg.fill("#pmAddToKitQty","2")
    pg.locator("input[data-bm='qty']").first.fill("5")
    pg.click("#pmSave"); pg.wait_for_timeout(250)
    c = cat(); newp = [x for x in c if x["name"]=="Fridge Magnet"][0]
    k = [x for x in c if x["id"]=="p4"][0]
    print("kit items:", k["kitItems"])
    assert any(i["productId"]==newp["id"] and i["qty"]==2 for i in k["kitItems"])
    # 3) create a product from inside a kit
    pg.evaluate("document.querySelectorAll('[data-kittoggle]').forEach(b=>b.click())")
    pg.locator("[data-editprod='p4']").first.click(); pg.wait_for_timeout(200)
    pg.click("#pmNewProd summary")
    pg.fill("#pmNpName","Gift Tag"); pg.fill("#pmNpPrice","1.5"); pg.fill("#pmNpGrams","4"); pg.fill("#pmNpQty","3")
    pg.click("#pmNpAdd"); pg.wait_for_timeout(250)
    c = cat(); gt = [x for x in c if x["name"]=="Gift Tag"][0]
    print("new product:", gt["bom"], gt["catalog"])
    assert gt["bom"] and gt["bom"][0]["qty"]==4
    pg.click("#pmSave"); pg.wait_for_timeout(250)
    k = [x for x in cat() if x["id"]=="p4"][0]
    print("kit items after:", k["kitItems"])
    assert any(i["productId"]==gt["id"] and i["qty"]==3 for i in k["kitItems"])
    b.close()
print("ERRORS:", errs)
