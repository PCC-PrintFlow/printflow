from playwright.sync_api import sync_playwright
import json
exec(open('test_n.py').read().split('\nerrs=[]\n')[0])
catalog.append({"id":"p9","name":"CWing Baby Dragon","part":"CW-BD","custPart":"","price":12,"catalog":"fair","bom":[{"materialId":"m1","qty":30}],"printHours":2,"laborMin":5,"extraCost":0})
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1366,"height":1000})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_settings_v1', JSON.stringify({machineRate:0.3, laborRate:20, targetMargin:50})); localStorage.setItem('pcc_fairs_v1', JSON.stringify({current:{name:'Test',date:'2026-11-14',method:'venmo',sales:[{id:'s1',price:12,time:new Date().toISOString(),method:'cash',productId:'p9',name:'CWing Baby Dragon'},{id:'s2',price:12,time:new Date().toISOString(),method:'venmo',productId:'p9',name:'CWing Baby Dragon'}]},history:[]})); }""", {"catalog":catalog,"mats":mats})
    pg.reload(); pg.wait_for_timeout(300)
    print("nav:", pg.eval_on_selector_all("nav.tabs button","e=>e.map(x=>x.innerText).join(' | ')"))
    st=lambda k: json.loads(pg.evaluate(f"localStorage.getItem('{k}')"))
    print("seed:", [(c["name"],c["shortId"]) for c in st('pcc_creators_v1')], "| p9 linked:", [x.get("creatorId") for x in st('pcc_catalog_v1') if x["id"]=="p9"])
    pg.click("button[data-tab='creators']"); pg.wait_for_timeout(200)
    # set fees: CWing monthly 8, Kong annual 60
    def edit(cid, fee, billing):
        pg.click(f"[data-credit='{cid}']"); pg.fill("#ceCrFee", str(fee)); pg.select_option("#ceCrBilling", billing); pg.click("#ceCrSave"); pg.wait_for_timeout(100)
    edit("cr_cinderwing", 8, "monthly"); edit("cr_kong3d", 60, "annual")
    print("summary:", pg.inner_text("#crSummary").replace("\n"," | "))
    print("rows:", pg.eval_on_selector_all(".cr-table tbody tr:not(.cr-prods)","rs=>rs.map(r=>r.innerText.replace(/\\s+/g,' '))"))
    # duplicate id
    pg.fill("#crName","Other"); pg.fill("#crId","cwing"); pg.click("#crAddBtn"); pg.wait_for_timeout(80)
    print("dup toast:", pg.inner_text("#toast"))
    pg.fill("#crId","Mythic3D"); pg.fill("#crName","Mythic"); pg.fill("#crFee","5"); pg.click("#crAddBtn"); pg.wait_for_timeout(80)
    print("count:", len(st('pcc_creators_v1')))
    pg.screenshot(path="cr_list.png")
    # new product via catalog add form with creator
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(150)
    pg.select_option("#catCreator", "cr_kong3d"); pg.fill("#catName","Articulated Gecko"); pg.fill("#catPrice","15")
    pg.click("#catAddBtn"); pg.wait_for_timeout(150)
    print("editor name:", pg.input_value("#pmName"), "| creator:", pg.eval_on_selector("#pmCreator","s=>s.options[s.selectedIndex].text"))
    # switch creator in editor
    pg.select_option("#pmCreator","cr_saber3d"); print("after switch:", pg.input_value("#pmName"))
    pg.select_option("#pmCreator",""); print("after none:", pg.input_value("#pmName"))
    pg.select_option("#pmCreator","cr_kong3d"); pg.click("#pmSave"); pg.wait_for_timeout(150)
    print("saved:", [(x["name"],x.get("creatorId")) for x in st('pcc_catalog_v1') if "Gecko" in x["name"]])
    # existing product: assign creator in editor
    pg.locator("#catalogListWrap [data-editprod='p2']").first.click(); pg.wait_for_timeout(150)
    pg.select_option("#pmCreator","cr_cinderwing"); pg.click("#pmSave"); pg.wait_for_timeout(150)
    print("sticker:", [x["name"] for x in st('pcc_catalog_v1') if x["id"]=="p2"])
    # rename CWing -> CW
    pg.click("button[data-tab='creators']"); pg.wait_for_timeout(150)
    pg.click("[data-credit='cr_cinderwing']"); pg.fill("#ceCrId","CW"); pg.click("#ceCrSave"); pg.wait_for_timeout(150)
    print("toast:", pg.inner_text("#toast"))
    print("names after rename:", sorted(x["name"] for x in st('pcc_catalog_v1') if x.get("creatorId")=="cr_cinderwing"))
    print("cw row:", pg.locator(".cr-table tbody tr", has_text="Cinderwing").first.inner_text().replace("\n"," "))
    pg.click("[data-crprods='cr_cinderwing']"); pg.wait_for_timeout(80)
    pg.screenshot(path="cr_list2.png")
    # prefix style
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(150)
    pg.select_option("#catCreator","cr_saber3d"); pg.fill("#catName","Saber Hilt"); pg.click("#catAddBtn"); pg.wait_for_timeout(150)
    print("part:", pg.input_value("#pmPart")); pg.click("#pmCancel")
    # delete creator
    pg.click("button[data-tab='creators']"); pg.wait_for_timeout(150)
    pg.click("[data-crdel='cr_kong3d']"); print("del msg:", pg.inner_text("#confirmText")[:90]); pg.click("#confirmOk"); pg.wait_for_timeout(100)
    print("gecko after delete:", [(x["name"],x.get("creatorId")) for x in st('pcc_catalog_v1') if "Gecko" in x["name"]])
    b.close()
print("ERRORS:", errs)
