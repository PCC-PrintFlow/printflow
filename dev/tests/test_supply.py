# Supply Ordering: tick = needs ordered, spool quantity, filters, New badge window, backup import, erase.
from playwright.sync_api import sync_playwright
import os, json, datetime, tempfile
SRC = os.environ["PRINTFLOW_HTML"]
today = datetime.date.today().isoformat()
old = (datetime.date.today() - datetime.timedelta(days=40)).isoformat()
s = open(SRC, encoding="utf-8").read()
a = '["B","PLA Basic","Bambu Green","00AE42","",""]'; c = '["B","PLA Basic","Beige","F7E6DE","",""]'
assert s.count(a) == 1 and s.count(c) == 1
s = s.replace(a, a.replace('"",""]', '"%s",""]' % today)).replace(c, c.replace('"",""]', '"%s",""]' % old))
tmp = os.path.join(tempfile.gettempdir(), "printflow_supply_test.html"); open(tmp, "w", encoding="utf-8").write(s)
html = "file://" + tmp
KEY = "pcc_supply_v1"
errs = []
def stored(pg): return json.loads(pg.evaluate("localStorage.getItem('%s')" % KEY) or "{}")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get("CHROME") or None, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width":1280,"height":1000})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(html); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_timeout(300)

    pg.click("button[data-tab='supply']"); pg.wait_for_timeout(150)
    assert pg.is_visible("#tab-supply")
    n_rows = pg.eval_on_selector_all(".sup-row", "e=>e.length"); print("rows shown:", n_rows)
    assert n_rows > 200
    assert pg.inner_text("#supSummary").split()[0] == "0"
    assert stored(pg) == {}, "nothing is stored until something is ticked"

    # New badge: only the one inside the window; the 40-day-old and baseline rows have none
    assert pg.eval_on_selector_all(".sup-new", "e=>e.length") == 1
    pg.check("#supNewOnly"); pg.wait_for_timeout(80)
    assert pg.eval_on_selector_all(".sup-row .sup-nm", "e=>e.map(x=>x.textContent)") == ["Bambu Green"]
    pg.uncheck("#supNewOnly")

    # tick = needs ordered, quantity box defaults to 1
    pg.fill("#supSearch", "Bambu Green"); pg.wait_for_timeout(80)
    assert pg.eval_on_selector_all(".sup-row", "e=>e.length") == 1
    assert pg.is_hidden("[data-sup-q]") if pg.query_selector("[data-sup-q]") else True
    pg.check("[data-sup-i]"); pg.wait_for_timeout(80)
    assert pg.input_value("[data-sup-q]") == "1"
    pg.fill("[data-sup-q]", "4"); pg.wait_for_timeout(80)
    assert stored(pg) == {"B|PLA Basic|Bambu Green": 4}, stored(pg)
    assert pg.inner_text("#supSummary").replace("\n", " ").startswith("1 need ordered 4 spools"), pg.inner_text("#supSummary")

    # a sold-out CookieCad color
    pg.fill("#supSearch", "Coral"); pg.wait_for_timeout(80)
    assert "sold out" in pg.inner_text(".sup-row").lower()
    pg.check("[data-sup-i]"); pg.fill("#supSearch", ""); pg.wait_for_timeout(80)

    # filters
    pg.check("#supNeedOnly"); pg.wait_for_timeout(100)
    names = pg.eval_on_selector_all(".sup-row .sup-nm", "e=>e.map(x=>x.textContent)"); print("needs ordered:", names)
    assert sorted(names) == ["Bambu Green", "Coral"]
    pg.select_option("#supSup", "C"); pg.wait_for_timeout(80)
    assert pg.eval_on_selector_all(".sup-row .sup-nm", "e=>e.map(x=>x.textContent)") == ["Coral"]
    pg.select_option("#supSup", "all"); pg.uncheck("#supNeedOnly")

    # an emptied quantity snaps back instead of storing nothing
    pg.fill("#supSearch", "Bambu Green"); pg.fill("[data-sup-q]", ""); pg.click("#supSearch"); pg.wait_for_timeout(80)
    assert pg.input_value("[data-sup-q]") == "4" and stored(pg)["B|PLA Basic|Bambu Green"] == 4
    pg.fill("#supSearch", "")

    # group buttons: Mark all / Clear act on the visible rows of that line
    pg.fill("#supSearch", "Aero"); pg.wait_for_timeout(80)
    pg.click("[data-sup-all]"); pg.wait_for_timeout(80)
    assert len([k for k in stored(pg) if "PLA Aero" in k]) == 2
    pg.click("[data-sup-clear]"); pg.wait_for_timeout(80)
    assert len([k for k in stored(pg) if "PLA Aero" in k]) == 0
    pg.fill("#supSearch", "")

    # order list text
    pg.click("#supCopyBtn"); pg.wait_for_timeout(100)
    txt = pg.input_value("#supOrderText"); print(txt)
    assert "BAMBU LAB" in txt and "PLA Basic: Bambu Green x4" in txt and "COOKIECAD" in txt and "Coral x1 (sold out)" in txt

    # persists across reload
    pg.reload(); pg.wait_for_timeout(300)
    assert stored(pg)["B|PLA Basic|Bambu Green"] == 4

    # importing a backup replaces supply data; an older backup without it clears it
    f_new = os.path.join(tempfile.gettempdir(), "sup_new.json"); f_old = os.path.join(tempfile.gettempdir(), "sup_old.json")
    json.dump({"settings":{}, "supply":{"C|Solid|Black":3}}, open(f_new, "w")); json.dump({"settings":{}}, open(f_old, "w"))
    pg.click("button[data-tab='settings']"); pg.wait_for_timeout(100)
    pg.set_input_files("#importFileInput", f_new); pg.wait_for_timeout(150); pg.click("#confirmOk"); pg.wait_for_timeout(250)
    assert stored(pg) == {"C|Solid|Black": 3}, stored(pg)
    pg.set_input_files("#importFileInput", f_old); pg.wait_for_timeout(150); pg.click("#confirmOk"); pg.wait_for_timeout(250)
    assert stored(pg) == {}, stored(pg)

    # erase all clears it
    pg.click("button[data-tab='supply']"); pg.fill("#supSearch", "Bambu Green"); pg.check("[data-sup-i]"); pg.fill("#supSearch", "")
    assert stored(pg) != {}
    pg.click("button[data-tab='settings']"); pg.click("#wipeDataBtn"); pg.wait_for_timeout(100); pg.click("#confirmOk"); pg.wait_for_timeout(250)
    assert stored(pg) == {}, stored(pg)
    b.close()
print("ERRORS:", errs)
