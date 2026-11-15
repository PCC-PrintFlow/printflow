from playwright.sync_api import sync_playwright
import json
exec(open('snap.py').read().split("with sync_playwright()")[0])
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1280,"height":900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_settings_v1', JSON.stringify({machineRate:0.3, laborRate:20, targetMargin:50})); }""", {"catalog":catalog})
    pg.reload(); pg.wait_for_timeout(300)
    print("nav:", pg.eval_on_selector_all("nav.tabs button","bs=>bs.map(b=>b.innerText)"))
    pg.click("button[data-tab='materials']"); pg.wait_for_timeout(150)
    print("materials tab visible:", pg.is_visible("#tab-materials"), "| catalog visible:", pg.is_visible("#tab-catalog"))
    def addmat(name,typ,price,qty,notes=""):
        pg.fill("#matName",name); pg.select_option("#matType",typ); pg.fill("#matPackPrice",price); pg.fill("#matPackQty",qty); pg.fill("#matNotes",notes); pg.click("#matAddBtn"); pg.wait_for_timeout(60)
    addmat("PLA","filament","19.99","1000","Bambu Basic"); addmat("Magnet 6x3mm","magnet","8.99","100"); addmat("M3x10 bolt","hardware","6.49","100")
    print("rows:", pg.locator("#materialListWrap tbody tr").count(), "| used-in:", pg.eval_on_selector_all("#materialListWrap tbody tr td.mat-used","c=>c.map(x=>x.innerText)"))
    # edit inline on materials tab
    pg.locator("[data-medit]").first.click(); pg.fill("tr[data-mrow] [data-mf='packPrice']","21.99"); pg.locator("[data-msave]").click(); pg.wait_for_timeout(80)
    print("after edit:", pg.inner_text("#materialListWrap tbody tr >> nth=0").replace("\t"," | ").replace("\n"," "))
    # search
    pg.fill("#materialSearch","magnet"); pg.wait_for_timeout(50); print("search rows:", pg.locator("#materialListWrap tbody tr").count()); pg.fill("#materialSearch","")
    # use in BOM from catalog
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(100)
    pg.locator("[data-editprod='p1']").last.click(); pg.wait_for_timeout(100)
    pg.click("#pmAddLine"); bid = pg.eval_on_selector("#pmBom select[data-bm='materialId']","e=>e.dataset.bid")
    print("BOM options:", pg.eval_on_selector(f"#bm-mat-{bid}","e=>[...e.options].map(o=>o.text)"))
    pg.select_option(f"#bm-mat-{bid}", index=1); pg.fill(f"#bm-qty-{bid}","12")
    pg.click("#pmAddLine"); bid2 = pg.eval_on_selector_all("#pmBom select[data-bm='materialId']","es=>es[1].dataset.bid")
    pg.select_option(f"#bm-mat-{bid2}", label=pg.eval_on_selector(f"#bm-mat-{bid2}","e=>[...e.options].find(o=>o.text.startsWith('Magnet')).text")); pg.fill(f"#bm-qty-{bid2}","2")
    pg.click("#pmSave"); pg.wait_for_timeout(100)
    # back to materials: used-in shows product and opens editor
    pg.click("#goMaterialsBtn"); pg.wait_for_timeout(100)
    print("used-in now:", pg.eval_on_selector_all("#materialListWrap tbody tr td.mat-used","c=>c.map(x=>x.innerText)"))
    pg.locator("[data-openprod]").first.click(); pg.wait_for_timeout(100)
    print("modal opened from materials:", pg.is_visible("#prodModal"), pg.input_value("#pmName"), "| bom lines:", pg.locator("#pmBom tbody tr").count())
    pg.click("#pmCancel")
    pg.screenshot(path="e_materials.png", full_page=True)
    b.close()
print("ERRORS:", errs)
