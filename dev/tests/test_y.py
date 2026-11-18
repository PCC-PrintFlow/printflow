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
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify([d.cust])); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_settings_v1', JSON.stringify({nextOrderNum:10, machineRate:0.3, laborRate:20, targetMargin:50})); }""", {"catalog":catalog,"cust":cust,"orders":orders,"mats":mats})
    pg.reload(); pg.wait_for_timeout(300)
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(150)
    st = lambda: json.loads(pg.evaluate("localStorage.getItem('pcc_catalog_v1')"))
    names = lambda: pg.eval_on_selector_all("#catalogListWrap tbody tr","rs=>rs.map(r=>r.children[0].innerText.replace(/\\n/g,' / '))")
    # notes + both on Sticker (p2)
    pg.locator("#catalogListWrap [data-editprod='p2']").first.click(); pg.wait_for_timeout(150)
    pg.fill("#pmNotes","Vinyl cutter, matte finish.\nBest seller in red."); pg.check("#pmCatBoth"); pg.click("#pmSave"); pg.wait_for_timeout(150)
    print("business list:", names())
    # copy keychain p1 to fair
    pg.evaluate("document.querySelectorAll('[data-kittoggle]').forEach(function(b){ if(b.getAttribute('aria-expanded')!=='true') b.click(); })")  # kits start collapsed
    pg.locator("#catalogListWrap [data-copyprod='p1']").first.click(); pg.wait_for_timeout(150)
    print("toast:", pg.inner_text("#toast"))
    pg.click("#catSwFair"); pg.wait_for_timeout(150)
    print("fair list:", names())
    pg.screenshot(path="y_fair.png")
    s1 = st(); print("stored:", [(x["name"],x["catalog"],x.get("notes","")[:12]) for x in s1 if x["id"] in ("p1","p2") or (x["name"]=="Keychain")])
    # change copy price independently
    cid = [x["id"] for x in s1 if x["name"]=="Keychain" and x["catalog"]=="fair"][0]
    pg.locator(f"#catalogListWrap [data-editprod='{cid}']").first.click(); pg.wait_for_timeout(150)
    pg.fill("#pmPrice","5"); pg.click("#pmSave"); pg.wait_for_timeout(150)
    print("prices:", [(x["name"],x["catalog"],x["price"]) for x in st() if x["name"]=="Keychain"])
    # remove 'both' Sticker from fair -> business only
    pg.locator("#catalogListWrap [data-delprod='p2']").first.click(); pg.wait_for_timeout(150)
    print("confirm:", pg.inner_text("#confirmModal") if pg.locator("#confirmModal").count() else "?")
    pg.click("#confirmOk") if pg.locator("#confirmOk").count() else None
    pg.wait_for_timeout(150)
    print("sticker after remove:", [x["catalog"] for x in st() if x["id"]=="p2"], "| fair list:", names())
    # print fair: no notes
    pg.click("#printCatalogBtn"); pg.wait_for_timeout(150)
    print("fair print rows:", pg.eval_on_selector_all("#catPrintItems tr","rs=>rs.map(r=>r.innerText.replace(/\\s+/g,' '))"))
    pg.evaluate("document.getElementById('closeCatalogPreviewBtn').click()")
    # order picker: no duplicate for 'both', copy appears in fair group
    pg.click("button[data-tab='neworder']"); pg.wait_for_timeout(150)
    print("picker:", pg.eval_on_selector("select.of-product","s=>[...s.querySelectorAll('optgroup')].map(g=>g.label+': '+[...g.children].map(o=>o.text).join(', '))"))
    b.close()
print("ERRORS:", errs)
