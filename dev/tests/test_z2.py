from playwright.sync_api import sync_playwright
exec(open('test_n.py').read().split('\nerrs=[]\n')[0])
catalog[0]["catalog"]="fair"
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    for w,h,n in [(820,1180,"z_ipad_p"),(1180,820,"z_ipad_l")]:
        pg = b.new_page(viewport={"width":w,"height":h}, has_touch=True)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(html)
        pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); }""", {"catalog":catalog,"mats":mats})
        pg.reload(); pg.wait_for_timeout(300)
        pg.click("button[data-tab='fairs']"); pg.wait_for_timeout(200)
        pg.click("[data-fitem='p1']"); pg.wait_for_timeout(1600)
        pg.screenshot(path=n+".png")
        pg.close()
    b.close()
print("ERRORS:", errs)
