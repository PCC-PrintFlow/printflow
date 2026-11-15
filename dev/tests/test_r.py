from playwright.sync_api import sync_playwright
import json, base64
exec(open('test_n.py').read().split('\nerrs=[]\n')[0])
orders[0]["items"][0]["notes"]="Gift boxed — names list emailed 11/2"
orders[0]["items"][0]["filamentSwaps"]={"m1":"m2"}
lines=[]
for i in range(38):
    lines.append({"productId":"p1","orderId":"o1","orderItemId":"i1" if i==0 else "","orderNumber":"ORD-PCC-2026-0007","orderName":"Fair batch","notes":("Engrave name #%d on back"%i) if i%5==0 else "","name":"Keychain (Filament: Silk PLA, Base: Red) style %d"%i,"part":"PCC-KC-01","custPart":"ACM-1","qty":2,"price":6.64,"extended":13.28})
inv={"id":"v1","invoiceNumber":"INV-PCC-2026-1004","date":"2026-11-12","dueDate":"2026-11-27","status":"sent","event":"Orders ORD-PCC-2026-0007 · Fair batch, ORD-PCC-2026-0008 · Holiday, ornaments","customerId":"c1","customer":cust,"lineItems":lines,"subtotal":504.64,"taxable":True,"taxRate":7,"taxAmount":35.32,"total":539.96,"notes":"Thank you! Payment due within 15 days. Checks payable to Pa Chuck Creations, LLC.","orderIds":["o1"]}
errs=[]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=__import__("os").environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1366,"height":900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html)
    pg.evaluate("""(d)=>{ localStorage.clear(); localStorage.setItem('pcc_catalog_v1', JSON.stringify(d.catalog)); localStorage.setItem('pcc_customers_v1', JSON.stringify([d.cust])); localStorage.setItem('pcc_orders_v1', JSON.stringify(d.orders)); localStorage.setItem('pcc_invoices_v1', JSON.stringify([d.inv])); localStorage.setItem('pcc_materials_v1', JSON.stringify(d.mats)); localStorage.setItem('pcc_settings_v1', JSON.stringify({nextOrderNum:10, invPrefix:'PCC', nextInvNum:1005, machineRate:0.3, laborRate:20, targetMargin:50, bizPhone:'260-555-0100'})); }""", {"catalog":catalog,"cust":cust,"orders":orders,"mats":mats,"inv":inv})
    pg.reload(); pg.wait_for_timeout(300)
    print("PDFLib loaded:", pg.evaluate("!!window.PDFLib"))
    pg.evaluate("window.claude={use:async()=>({save:async(o)=>{ window.__name=o.filename; window.__pdf=Array.from(o.data); return {status:'saved'}; }})}")
    pg.click("button[data-tab='invoices']"); pg.wait_for_timeout(100)
    pg.locator("#invoiceListWrap [data-print]").first.click(); pg.wait_for_timeout(200)
    pg.click("#pdfNowBtn"); pg.wait_for_timeout(1500)
    name=pg.evaluate("window.__name"); data=bytes(pg.evaluate("window.__pdf")); open("/tmp/"+name,"wb").write(data)
    print("invoice pdf:", name, len(data), "toast:", pg.inner_text("#toast"))
    pg.evaluate("document.getElementById('closePreviewBtn').click()")
    pg.click("button[data-tab='orders']"); pg.wait_for_timeout(100)
    pg.locator("#orderListWrap tr", has_text="ORD-PCC-2026-0007").locator("[data-oview]").first.click() if pg.locator("#orderListWrap [data-oview]").count() else None
    pg.wait_for_timeout(200)
    vis = pg.evaluate("getComputedStyle(document.getElementById('orderPrintArea')).display")
    print("order preview display:", vis)
    pg.click("#pdfOrderNowBtn"); pg.wait_for_timeout(1500)
    name2=pg.evaluate("window.__name"); data2=bytes(pg.evaluate("window.__pdf")); open("/tmp/"+name2,"wb").write(data2)
    print("order pdf:", name2, len(data2))
    b.close()
print("ERRORS:", errs)
