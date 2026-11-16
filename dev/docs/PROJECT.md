# PCC PrintFlow: project handoff

*Updated 2026-11-15. Carried over from the earlier Claude Project "Invoice Gneterator", where the app was built.*

PCC PrintFlow runs Pa Chuck Creations, LLC (10819 Walnut St., Leo, IN 46765; PaChuckCreations@gmail.com), a 3D-printing business. It covers:

- Order forms and production tracking.
- Invoices.
- Product costing: bill of materials, batch prints, purge block credit.
- Kits.
- Two catalogs: the business Product Catalog and the Craft Fair Catalog.
- Creator (design subscription) tracking.
- A Craft Fairs sales tracker.
- Per-order filament choice.
- Profit-margin tracking.

It started as an "Invoice Generator" and was renamed **PCC PrintFlow** on 2026-11-11.

## Where everything lives

| Thing | Where |
| --- | --- |
| GitHub account | **`pcc-printflow`** |
| App + source (public) | `pcc-printflow/printflow`. GitHub Pages: https://pcc-printflow.github.io/printflow/ |
| Synced business data (**private**) | `pcc-printflow/printflow-data`, holding the single file `printflow-data.json` |
| Installed app | On the owner's PC (Chrome/Edge) and iPad (Home Screen web app). Both installed and synced 2026-11-15. |
| Claude artifact (same source, runs inside Claude) | https://claude.ai/artifact/Ekg1aKxo3gFSEBqzVgvMSG, slug `6f5fd34d-5c61-434e-b0e7-406e56d4ee01` |
| Install & sync setup guide (doc) | https://claude.ai/artifact/59ETDuUXFJKxJb9z8Cowqf |
| Side-menu design options | https://claude.ai/artifact/1LMXcriTPUUKQgR2zR4nTF |

The owner now works in the **installed app**. The Claude artifact is a preview/test copy; its data is separate.

## Development workflow

1. **Source:** `dev/printflow.html` is one self-contained HTML/JS file, about 940 KB, mostly the embedded pdf-lib 1.17.1 at the end of the body. There's no framework and no build step for the source itself.
2. **Build:** `python3 dev/build.py` writes the installable app to the repo root:
   - `index.html` = the source plus `window.PCC_STANDALONE=true`, `window.PCC_APP_VERSION`, the manifest/Apple meta tags and the service-worker registration.
   - `sw.js` (versioned cache; network-first for the page with a 4 s fallback to cache).
   - `manifest.webmanifest` and the icons.
3. **Test:** `python3 dev/tests/run_all.py`.
   - Playwright scripts that load the source (or the built app, for `test_pwa.py`) with made-up data. Each prints what it sees and ends with `ERRORS: [...]`; the runner fails a test on page or console errors. `test_pwa.py` expects 3 console errors: the fake 401/404 responses it sends on purpose.
   - Set `CHROME=/path/to/chrome` to use an installed Chrome.
   - When adding a feature, add a `test_<x>.py` alongside the others. Many tests reuse fixtures by `exec`-ing the top of `test_n.py`, `test_g.py`, `snap.py`, etc.
4. **Ship:**
   - Commit and push. Pages redeploys in a few minutes, and devices pick up the update on the next online launch (close and reopen if needed). The version shows at the bottom of Settings → Sync.
   - Optionally republish `dev/printflow.html` to the Claude artifact (slug above) so the in-Claude copy matches.
5. **Editing tips:**
   - Make edits with anchored find/replace, asserting each anchor matches exactly once.
   - Check for duplicate function names after adding functions. A duplicate once silently overrode another function.
   - Inside Claude artifacts, U+FFFD literals are rejected, so they're escaped as `"�"` in pdf-lib.

### Rules that keep owners' data safe

- Never put business data in the public repo. Never read or write `printflow-data` while developing.
- Don't rename localStorage keys or change the sync payload without a migration. Existing devices hold real data.
- New data collections must be added in four places: Export Backup, `applyBackupData` (Import/Pull), `syncDataObject()` (Push) and Erase All Data.
- The sync token and repo name live only in `pcc_sync_v1` on each device. Never include them in backups or pushes.

## Architecture notes

- **Storage:** localStorage keys:
  - Data: `pcc_settings_v1`, `pcc_customers_v1`, `pcc_catalog_v1`, `pcc_invoices_v1`, `pcc_orders_v1`, `pcc_materials_v1`, `pcc_fairs_v1`, `pcc_creators_v1`.
  - View state: `pcc_catview_v1`, `pcc_orderlist_view_v1`.
  - Device-only sync settings: `pcc_sync_v1`.
- **Helpers:** `save(key,value)`, `load`, `persistAll()`, `uid()`, `money()`, `fmtDate()`, `todayISO()`, `escapeHtml()`, `toast(msg,ms)`, `askConfirm(title,text,onOk,okLabel)`.
- **Downloads:** go through `getDownloads()`.
  - Inside Claude it uses `window.claude.use("downloads")`, a declared artifact capability. Claude's CSP blocks fetch to other hosts, and `window.print` is blocked there.
  - In the installed app it uses `LOCAL_DOWNLOADS`: `a[download]`, or the Share sheet on the iPad.
- **Printing:** in the installed app, print opens from a hidden iframe. Inside Claude it downloads an HTML file to print.
- **PDF:** `buildPdf(doc)` is the generic builder.
  - Input: heading, meta, optional blockTitle/blockLines, columns, rows (arrays or `{fill, cells}`, parts with `indent`), totals `[label, value, grand]`, notes, footer, contLabel.
  - Output: a repeating table header, "Page X of Y", and the logo (canvas → PNG).
- **Costs:** `productCost(p, seen, swaps)` returns `{materials, machine, labor, extra, components, total, perPrint, printMaterials, printMachine, gross, purge, purgeAll, noPurgeTotal, hasData, incomplete, missing}`.
- **Product fields:** `catalog` ("business" / "fair" / "both"), `notes`, `creatorId`, `perPrint`, `makesPurge`, `purgePerBlock`, `bom`, `isKit`, `kitItems`, `printHours`, `laborMin`, `extraCost`, `custPart`.
- **Settings:** `machineRate` 0.30, `laborRate` 20, `targetMargin`, `purgeBlockPrice` 5, `fairTaxRate` 7, `venmoFixed` 0.09, `venmoPct` 2.29, .
- **Catalog helpers:** `isFair`, `isBusiness`, `inCatView`, `catalogKitGroups`, `groupedProductOptionsHtml`, `defaultFilament()`.
- **Fairs:** `fairs = {current:{name,date,method,sales:[{id,price,time,method,productId,name}]}, history:[… + rates, closedAt, importedAt?]}`. Functions: `fairTotals`, `fairCsv`, `fairSalesPdfDoc`, `saveFairFile`, `parseFairCsv`.
- **Creators:** each is `{id, name, shortId, billing, fee, url, notes, active}`. Functions: `creatorCost`, `creatorSales12`, `withCreatorPrefix`, `stripCreatorPrefix`, `nameHasCreatorPrefix`, `validShortId`.
- **Sync:**
  - API: GitHub Contents API on `printflow-data.json` (GET with `application/vnd.github+json` for the sha, `application/vnd.github.raw+json` for the content; PUT with base64 UTF-8 and the sha).
  - Payload: `{format:"pcc-printflow-sync", version:1, pushedAt, device, data:{settings, customers, catalog, materials, invoices, orders, fairs, creators}}`.
  - Functions: `doPush`, `doPull`, `doSyncTest`, `fetchRemote`, `syncDataObject`, `localDataHash`, `applyBackupData`.

## Features

### Installable app + Push/Pull sync (2026-11-14)
- The owner wanted push/pull between PC and iPad, not real-time sync.
- **Settings → Sync between devices:** device name, data repo, fine-grained token (Contents: Read and write on `printflow-data` only).
  - **Push** writes the whole dataset. **Pull** replaces the device's data after a summary confirm. Nothing is merged.
  - Safeguards:
    - "Cloud copy is newer than this device's last sync" → **Push anyway**.
    - A warning before pulling over unpushed changes.
    - The status line shows "has changes not pushed yet".
    - Test connection warns if the repo is public.
  - Every push is a commit, so history keeps old versions. Inside Claude the panel is disabled with a note.
- **Installed-app behavior:**
  - Works offline.
  - 🖨 Print opens the print dialog directly.
  - Downloads are normal; on the iPad the Share sheet opens.
  - `navigator.storage.persist()`.
  - The version shows in the Sync panel.
- **Decision (2026-11-15):** both devices share one token, for now.
- **Reminders (2026-11-15):** weekly sync reminder (Sundays, evening) and a one-time token-expiry reminder on 2027-11-01, both set as Claude scheduled tasks (push notifications). They are not built into the app.

### Creators (design subscriptions, 2026-11-14)
- **Records → Creators:** designers whose files the owner sells prints of: **Saber3D**, **Kong3D**, **Cinderwing (CWing)** (pre-seeded).
- Each creator has:
  - A unique **Short ID** (case-insensitive; letters, numbers, - and _; 16 characters or fewer).
  - **Billing** (Monthly or Annual) and **Fee**.
  - Website, Notes, **Active**.
- **Summary bar:** total per month and per year of active subscriptions.
- **List:** per-month and per-year fee; product count (expandable; click to edit a product); **Sales (12 mo)** (invoices before tax + fair sales with tax backed out), with "covers the fee" or "$X short".
- **Products link** via `creatorId`. As of 2026-11-16 the short ID is the prefix of the **Part #**, not of the product name:
  - Part # style is always "CWG-123" (a hyphen). Names are left clean.
  - Picking a creator in the product editor prefixes the Part # (and swaps/removes it when the creator changes). A Part # that is only the prefix is saved as blank.
  - Changing a short ID re-prefixes that creator's Part #s. Deleting a creator un-links its products but keeps their Part #s.
  - There is no automatic migration: existing products named with the ID in front are edited by hand (a one-time clean-up button was built and then removed at the owner's request).

### Craft Fairs (sales tracker, 2026-11-14)
- Built from the owner's standalone iPad tracker (`craft-fair-tracker-standalone_5.html`). Located at Work → Craft Fairs.
- **Top bar:** fair name, date, **Close Out Fair & Save**, Export CSV, Save as PDF, Clear all sales.
- **Logging a sale:**
  - Cash/Venmo toggle (Venmo is the default).
  - Craft Fair Catalog item buttons.
  - Quick prices $1–$15 and Custom.
- **Multi-item sale (2026-11-16):** the **Multi-item sale** toggle turns taps (catalog items and quick prices) into a "Current sale" cart with +/− quantities; **Log Venmo/Cash sale** records it as one transaction (one Venmo fee). With the toggle off, one tap still logs one sale.
  - Stored as a normal sale plus optional `lines: [{productId, name, qty, unit}]`; `price` is the total and `name` is a summary ("Dragon; Keychain x2"). Old sales and the sync format are unchanged. "Items sold" and "Sold by item" count quantities; profit estimates use each line's cost and share the fee by revenue.
  - CSV/PDF show the summary in the Item column; importing the CSV rebuilds the lines when every part matches a Craft Fair item and the prices add up. Test: `test_multi.py`.
- **Totals:**
  - Items sold, cash, Venmo.
  - Taxable (gross ÷ 1.07) and tax due.
  - Total collected.
  - Venmo fees ($0.09 + 2.29% per Venmo sale).
  - Net deposit.
  - Screen-only est. profit on catalog items.
  - Sold by item.
- **Past fairs:** Details, CSV, PDF, Reopen and ✕.
  - **Import fair CSV…** takes tracker or PrintFlow CSVs (several at once). It keeps times, methods and rates, matches items by name, and marks fairs "Imported from CSV".
  - Deer Ridge (2026-10-24): 27 sales, $432.00 collected, $28.26 tax, $8.20 fees, $423.80 net (verified).
- **Settings → Craft Fairs:** tax 7% (Indiana), Venmo $0.09 and 2.29%.
- **Files:** CSV `pa-chuck-creations-<fair>-<date>-sales.csv` (tracker format + Item column); PDF `craft-fair-<fair>-<date>.pdf`.

### Two catalogs
- **Product Catalog** = items sold mostly to businesses; **Craft Fair Catalog** = fair items. `catalog: "business" | "fair" | "both"`.
- A switch at the top of the section. Each view has its own intro, margin summary, add form, kit-grouped list and print/PDF.
- **Both** = same item and price in both catalogs. **Copy to Fair / Copy to Product** makes an independent copy.
- Order/invoice pickers show business items grouped by kit, then a "Craft Fair Catalog" group.

### Costs, BOM & margins
- **Materials:** filament by type, magnets, hardware, etc., with package price and size. Default filament for new products is **PLA Basic**.
- **Product editor fields:**
  - Name, Part #, Customer Part #, Default Price.
  - Catalog and Creator.
  - Notes (internal, never printed).
  - Single / Kit.
  - **Pieces per print**.
  - Bill of Materials and Other costs.
  - **Makes purge blocks**.
  - Cost summary.
- **Batch prints:** filament and print time are entered for the whole print and divided by the pieces. Hands-on and other costs are per piece.
- **Purge block credit:** block price ($5, in Settings) ÷ pieces per block is subtracted from cost ("Net cost per piece"). A **secondary margin "if block doesn't sell"** shows the margin without the credit (`noPurgeTotal`).
- **Rates:** machine $0.30/print hour, labor $20/hour, target margin (50% recommended).
- **Margin** = (price − net cost) ÷ price. Shown as chips, in catalog columns, in the invoice Profit check and in history Margin (live costs).

### Parts and plates (2026-11-16)
- Each Bill of Materials line has an optional **Item name** (Body, Head, Top, Bottom…; suggestions offered, any text allowed) and **Plate #**.
- With **two or more distinct plate numbers** on a product, the single print-time field is replaced by one **Plate N print time (hours)** field per plate. `printHours` stays the sum of them, so costing, sync and backups work as before; per-plate times are stored in `plateHours` (`{"1":2,"2":1.5}`). Going from one plate to several carries the existing time onto the first plate.
- New optional fields (no migration): BOM line `part`, `plate`; product `plateHours`. Test: `test_plates.py`.

### Kits
- Bundles of products with quantities, extras and kit-level costs; nesting allowed. Grouped by kit everywhere products are listed, with kit names in **bold**. A kit is one line on orders and invoices.

### Orders → invoices (core workflow)
- Invoices only come from finished order items ("Invoice this item" → "Create Invoice"). Items from other orders can be added.
- **Item statuses:** Waiting Print, Partial, Pending Design, Waiting Response, Waiting Material, Done <date>, Delivered <date>.
- Create Invoice saves the order and pre-fills items (filament, colors, notes, pricing), customer and Event ("Orders ORD-… · name"). Deleting an invoice releases its items; double-invoicing is blocked.
- **Filament choice per order item** (premium filament): price keeps the catalog margin (new cost ÷ (1 − margin)). It's carried to the invoice and printed on order forms.
- Order item notes copy to invoice lines. An optional **Order name** is shown wherever the order # appears.
- Items (whole or part quantity) can move to a new or existing order.
- **Numbering:** `INV-<Code>-<Year>-<N>`, `ORD-<Code>-<Year>-<N>`. Invoices have tax, due date, and Draft/Sent/Paid status.
- **Order list:** search, item-status filter, Orders and Group-by-status views.
- **Customers:** Business Name, Contact, Phone, E-Mail, Address. Saved details sync into orders and invoices.

### Look & output
- **Side menu "Workshop Dark":** charcoal #1c2220, PC logo tile, green current section.
  - **Work:** New Order Form, Order Forms, Invoices, Craft Fairs.
  - **Records:** Customers, Product Catalog, Creators, Materials.
  - **Settings** at the bottom.
  - At 900 px or less it becomes a compact top bar.
- **Logo:** "PC Creations" blue monogram (transparent PNGs from a photo mockup; an SVG would print crisper). Used in the menu, on printouts and PDFs, as the tab icon and as the app icons. The accent color is still green.
- **Save as PDF:** invoices, order forms, catalogs and fairs. Letter size, logo, repeating header, rows never split, "Page X of Y". Never includes costs, margins, profit or product notes.

## Open items / ideas
- Creator fees aren't included in product costs (a per-piece licensing share could be added). Sales (12 mo) misses kits containing a creator's products unless the kit itself is tied to the creator.
- Filament choice swaps material price only. "Both" items share one price.
- No on-hand inventory yet.
- Older invoice lines without order links show no order refs.
- Possible next steps:
  - Inventory.
  - Price-tag sheet from the Craft Fair Catalog.
  - Fair comparison report.
  - Purge by grams.
  - A separate fair price for "both" items.
  - Logo-blue accent.
  - Production sheet.
  - Materials-needed totals.
  - Frozen costs on invoices.
  - Confirmation pop-up on the iPad before changes that will later be pushed to the PC's data (a reminder that edits may end up in the synced data; both devices are the owner's, but the iPad's user sometimes needs the nudge).
