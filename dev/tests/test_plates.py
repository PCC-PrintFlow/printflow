from playwright.sync_api import sync_playwright
import json, os
html = "file://"+os.environ["PRINTFLOW_HTML"]
mats=[{"id":"m1","name":"PLA Basic","type":"filament","unit":"g","packPrice":20,"packQty":1000,"notes":""},
      {"id":"m2","name":"PLA Red","type":"filament","unit":"g","packPrice":20,"packQty":1000,"notes":""}]
catalog=[{"id":"p1","name":"Owl","part":"","custPart":"","price":10,"bom":[{"id":"b1","materialId":"m1","qty":10}],"printHours":2,"laborMin":0,"extraCost":0}]
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1280,"height":900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_settings_v1', JSON.stringify({machineRate:0.3, laborRate:20, targetMargin:50})); }""", {"catalog":catalog,"mats":mats})
    pg.reload(); pg.wait_for_timeout(300)
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(150)
    pg.locator("[data-editprod]").first.click(); pg.wait_for_timeout(200)
    assert pg.is_visible("#pmHours") and not pg.is_visible("#pmPlateBox")
    pg.fill("[data-bm='part']", "Body"); pg.fill("[data-bm='plate']", "1")
    pg.click("#pmAddLine"); pg.wait_for_timeout(100)
    pg.locator("[data-bm='part']").nth(1).fill("Head")
    pg.locator("[data-bm='plate']").nth(1).fill("2")
    pg.locator("[data-bm='materialId']").nth(1).select_option("m2")
    pg.locator("[data-bm='qty']").nth(1).fill("5")
    assert not pg.is_visible("#pmHours") and pg.is_visible("#pmPlateBox")
    assert pg.input_value("#pm-plate-h-1")=="2", "existing hours carried to plate 1"
    pg.fill("#pm-plate-h-2","1.5")
    print("summary:", pg.inner_text("#pmSummary").replace("\n"," | ")[:300])
    pg.click("#pmSave"); pg.wait_for_timeout(200)
    c = json.loads(pg.evaluate("localStorage.getItem('pcc_catalog_v1')"))[0]
    print("saved:", c["bom"], c["plateHours"], c["printHours"])
    assert c["printHours"]==3.5 and c["plateHours"]=={"1":2,"2":1.5}
    assert c["bom"][0]["part"]=="Body" and c["bom"][1]["plate"]=="2"
    pg.reload(); pg.wait_for_timeout(250)
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(150)
    pg.locator("[data-editprod]").first.click(); pg.wait_for_timeout(200)
    assert pg.input_value("#pm-plate-h-2")=="1.5"
    pg.screenshot(path="plates.png")
    pg.fill("[data-bm='plate'] >> nth=1", "1"); pg.wait_for_timeout(100)
    assert pg.is_visible("#pmHours") and pg.input_value("#pmHours")=="3.5"
    print("OK")
print("ERRORS:", errs)
