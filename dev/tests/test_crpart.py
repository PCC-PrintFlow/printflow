from playwright.sync_api import sync_playwright
import json, os
html = "file://"+os.environ["PRINTFLOW_HTML"]
mats=[{"id":"m1","name":"PLA","type":"filament","unit":"g","packPrice":20,"packQty":1000,"notes":""}]
crs=[{"id":"c1","name":"Cinderwing","shortId":"CWing","billing":"monthly","fee":8,"url":"","notes":"","active":True},
     {"id":"c2","name":"Kong3D","shortId":"Kong","billing":"monthly","fee":5,"url":"","notes":"","active":True}]
def P(i,n,part,cid=None): 
    d={"id":i,"name":n,"part":part,"custPart":"","price":5,"bom":[],"printHours":0,"laborMin":0,"extraCost":0}
    if cid: d["creatorId"]=cid
    return d
cat=[P("a","CWing - Baby Dragon","BD-01","c1"), P("b","Kong Gecko","","c2"), P("c","CWing: Owl","CWing-07"),
     P("d","Plain Keychain","KC-1"), P("e","[Kong] Frog","Kong 9")]
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1280,"height":900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.cat)); localStorage.setItem('pcc_creators_v1', JSON.stringify(d.crs)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_settings_v1', JSON.stringify({machineRate:0.3})); }""", {"cat":cat,"crs":crs,"mats":mats})
    pg.reload(); pg.wait_for_timeout(300)
    # editor: picking a creator prefixes the part, name untouched
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(150)
    pg.locator("[data-editprod='d']").first.click(); pg.wait_for_timeout(150)
    pg.select_option("#pmCreator","c2")
    assert pg.input_value("#pmPart")=="Kong-KC-1" and pg.input_value("#pmName")=="Plain Keychain"
    pg.select_option("#pmCreator","c1"); assert pg.input_value("#pmPart")=="CWing-KC-1"
    pg.select_option("#pmCreator",""); assert pg.input_value("#pmPart")=="KC-1"
    pg.select_option("#pmCreator","c1"); pg.click("#pmSave"); pg.wait_for_timeout(150)
    # rename creator ID
    pg.click("button[data-tab='creators']"); pg.wait_for_timeout(150)
    pg.click("[data-credit='c1']"); pg.fill("#ceCrId","CW"); pg.click("#ceCrSave"); pg.wait_for_timeout(150)
    print("toast:", pg.inner_text("#toast"))
    got={x["id"]:(x["name"],x["part"]) for x in json.loads(pg.evaluate("localStorage.getItem('pcc_catalog_v1')"))}
    assert got["d"][1]=="CW-KC-1" and got["a"][1]=="BD-01", got
    assert got["b"][1]=="" and got["e"][1]=="Kong 9"
    print("OK")
print("ERRORS:", errs)
