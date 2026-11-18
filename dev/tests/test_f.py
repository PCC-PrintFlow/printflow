from playwright.sync_api import sync_playwright
import json
exec(open('snap.py').read().split("with sync_playwright()")[0])
mats=[{"id":"m1","name":"PLA","type":"filament","unit":"g","packPrice":20,"packQty":1000,"notes":""},
      {"id":"m2","name":"Gift bag","type":"other","unit":"each","packPrice":10,"packQty":50,"notes":""}]
catalog[0].update({"bom":[{"id":"b1","materialId":"m1","qty":12}],"printHours":0.75,"laborMin":2,"extraCost":0})   # keychain $6
catalog[2].update({"bom":[{"id":"b2","materialId":"m1","qty":60}],"printHours":3,"laborMin":5,"extraCost":0})     # tray $14
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1280,"height":900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_customers_v1', JSON.stringify(d.customers)); localStorage.setItem('pcc_settings_v1', JSON.stringify({machineRate:0.3, laborRate:20, targetMargin:50})); }""", {"catalog":catalog,"mats":mats,"customers":customers})
    pg.reload(); pg.wait_for_timeout(300)
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(100)
    pg.fill("#catName","Quilter Starter Kit"); pg.fill("#catPart","PCC-KIT-01"); pg.fill("#catPrice","22")
    pg.click("#catAddKitBtn"); pg.wait_for_timeout(150)
    print("title:", pg.inner_text("#pmTitle"), "| kit radio:", pg.is_checked("#pmTypeKit"), "| bom title:", pg.inner_text("#pmBomTitle")[:30])
    k1 = pg.eval_on_selector("#pmKit select[data-km='productId']","e=>e.dataset.kid")
    print("kit options:", pg.eval_on_selector(f"#km-p-{k1}","e=>[...e.options].map(o=>o.text)"))
    pg.select_option(f"#km-p-{k1}", "p1"); pg.fill(f"#km-q-{k1}","2")
    pg.click("#pmAddKitLine"); k2 = pg.eval_on_selector_all("#pmKit select[data-km='productId']","es=>es[1].dataset.kid")
    pg.select_option(f"#km-p-{k2}", "p3"); pg.fill(f"#km-q-{k2}","1")
    pg.click("#pmAddLine"); bid = pg.eval_on_selector("#pmBom select[data-bm='materialId']","e=>e.dataset.bid")
    pg.select_option(f"#bm-mat-{bid}","m2"); pg.fill(f"#bm-qty-{bid}","1"); pg.fill("#pmLabor","3")
    print("compare:", pg.inner_text("#pmKitCompare"))
    print("summary:", pg.inner_text("#pmSummary").replace("\n"," | "))
    pg.screenshot(path="f_kitmodal.png")
    pg.click("#pmSave"); pg.wait_for_timeout(150)
    rows = pg.eval_on_selector_all("#catalogListWrap tbody tr","rs=>rs.map(r=>[...r.children].slice(0,6).map(c=>c.innerText.replace(/\\n/g,' / ')).join(' | '))")
    for r in rows: print("  ", r)
    kitid = pg.evaluate("JSON.parse(localStorage.getItem('pcc_catalog_v1')).find(p=>p.isKit).id")
    # loop prevention: edit keychain, switch to kit, options must not include the starter kit
    pg.evaluate("document.querySelectorAll('[data-kittoggle]').forEach(function(b){ if(b.getAttribute('aria-expanded')!=='true') b.click(); })")  # kits start collapsed
    pg.locator("[data-editprod='p1']").last.click(); pg.wait_for_timeout(100)
    pg.check("#pmTypeKit"); pg.wait_for_timeout(50)
    opts = pg.eval_on_selector("#pmKit select[data-km='productId']","e=>[...e.options].map(o=>o.text)")
    print("keychain-as-kit options (should exclude itself & Starter Kit):", opts)
    pg.click("#pmCancel")
    # nested: second kit containing the first kit
    pg.fill("#catName","Deluxe Bundle"); pg.fill("#catPrice","40"); pg.click("#catAddKitBtn"); pg.wait_for_timeout(100)
    kk = pg.eval_on_selector("#pmKit select[data-km='productId']","e=>e.dataset.kid")
    pg.select_option(f"#km-p-{kk}", kitid); pg.fill(f"#km-q-{kk}","1")
    print("nested summary total:", [l for l in pg.inner_text("#pmSummary").split("\n") if "Total" in l or "$" in l][:4])
    pg.click("#pmSave"); pg.wait_for_timeout(100)
    # the starter kit must not be able to include Deluxe Bundle
    pg.locator(f"[data-editprod='{kitid}']").last.click(); pg.wait_for_timeout(100)
    print("starter kit options:", pg.eval_on_selector("#pmKit select[data-km='productId']","e=>[...e.options].map(o=>o.text.split(' —')[0])"))
    pg.click("#pmCancel")
    # order with kit + invoice profit
    pg.click("button[data-tab='neworder']"); pg.wait_for_timeout(100)
    pg.fill("#ordCustPicker","Acme"); pg.wait_for_timeout(100); pg.locator("#ordCustSuggestions div[data-cid]").first.dispatch_event("mousedown"); pg.wait_for_timeout(100)
    sel = pg.locator("select.of-product").first; sel.select_option(kitid); pg.wait_for_timeout(100)
    print("order meta:", pg.inner_text(".of-meta").replace("\n"," "))
    st = pg.locator("select[data-ostatus]").first; st.select_option("done"); pg.wait_for_timeout(80)
    pg.locator("[data-oselect]").first.click(); pg.wait_for_timeout(80)
    pg.click("#createInvFromOrderBtn"); pg.wait_for_timeout(300)
    print("invoice profit:", pg.inner_text("#profitBody").replace("\n"," | "))
    pg.click("#saveInvoiceBtn"); pg.wait_for_timeout(150)
    # delete keychain -> removed from kit
    pg.click("button[data-tab='catalog']"); pg.wait_for_timeout(100)
    pg.locator("[data-delprod='p1']").click(); pg.wait_for_timeout(100)
    print("confirm text:", pg.inner_text("#confirmMsg") if pg.locator("#confirmMsg").count() else pg.inner_text(".modal-backdrop[style*='flex'] .modal"))
    pg.locator("#confirmOk").click(); pg.wait_for_timeout(100)
    kit = pg.evaluate("JSON.parse(localStorage.getItem('pcc_catalog_v1')).find(p=>p.name==='Quilter Starter Kit')")
    print("kit items after delete:", kit["kitItems"])
    pg.click("#printCatalogBtn"); pg.wait_for_timeout(200)
    print("catalog print:", pg.eval_on_selector_all("#catPrintItems tr","rs=>rs.map(r=>r.children[0].innerText.replace(/\\n/g,' / '))"))
    b.close()
print("ERRORS:", errs)
