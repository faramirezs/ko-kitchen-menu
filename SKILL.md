---
name: kokitchen-menu
description: "Weekly KoKitchen lunch-menu publishing pipeline. Data-driven generator in the ko-kitchen-menu repo: edit per-location JSONs (dishes, EN/DE titles and descriptions, allergen codes, prices, week label/dates), render one-A4 print menus for both locations (KK and SRH), generate SumUp POS import CSVs, verify layout in a browser, commit and push so GitHub Pages serves them. Use when the user asks to update the weekly menu, change any dish/title/description/allergen/price/week date, regenerate the print menus, or produce the POS import files."
allowed-tools: Bash(python3:*), Bash(git:*), Bash(gh:*)
---

# KoKitchen weekly menu pipeline

Single source of truth: two JSON files drive everything. `render.py`
produces the print menus (one template, two locations), `pos_import.py`
produces the SumUp POS import CSVs. All generated files are committed to
the same repo; GitHub Pages auto-deploys the HTML.

## Repo layout

```
kk-menu.json      KK menu data (daily curry box + Mon-Thu, no prices on sign)
srh-menu.json     SRH menu data (Mon-Thu, per-item prices)
template.html     shared A4 design with {{PLACEHOLDERS}}
render.py         python3 render.py kk|srh  ->  <loc>-print-menu.html
pos_import.py     python3 pos_import.py     ->  kk-pos-import.csv + srh-pos-import.csv
kk-print-menu.html / srh-print-menu.html    GENERATED - never hand-edit
kk-pos-import.csv / srh-pos-import.csv      GENERATED - never hand-edit
```

The repo must live OUTSIDE any sync folder (e.g. Nextcloud) - `.git`
corrupts under sync. Generated files are derived; only the JSONs are edited.

## What you need

- Python 3 (stdlib only - csv, json, pathlib; no pip packages)
- `git` + `gh` authenticated with push access to `faramirezs/ko-kitchen-menu`
- Browser to open `file://` URLs of the rendered menus for verification

## Data model

`days[]`: each has `title_en`/`title_de` (MONDAY/MONTAG) and `items[]`.

Each item: `name_en`, `desc_en`, `name_de`, `desc_de`, `allergens[]`
(LMIV codes: A gluten, F soya, L celery, M mustard, C egg, G milk - full
titles in `ALLERGEN_TITLES` in render.py), and `price` **SRH only**
(German format `"9,90 €"`). KK items carry NO price - the KK sign shows
no prices; the POS CSV derives them from SRH.

KK only: `daily` object = the daily curry box, shown once on the sign.
Optional `daily.pos[]` = POS-only split items, e.g.:

```json
"daily": {
  "name_en": "KoKitchen Signature Curry with Basmati Rice",
  "desc_de": "Fruchtige Ananasnoten, saisonales Gemüse, mariniertes Sonnenblumenprotein.",
  "note_de": "Auch erhältlich mit zart mariniertem Hähnchen (halal) anstelle von Sonnenblumenprotein.",
  "allergens": ["F"],
  "pos": [
    {"name": "KK Curry Vegan",   "price": "9,90 €", "desc": "..."},
    {"name": "KK Curry Chicken", "price": "10,90 €", "desc": "..."}
  ]
}
```

`daily.pos` does NOT appear on the sign - it only feeds the POS CSV.

Text conventions: German descriptions are terse list-style
("Fruchtige Ananasnoten, saisonales Gemüse, mariniertes
Sonnenblumenprotein."); English is a sentence. Prices use German comma
format on the sign and in JSON (`9,90 €`); the CSV generator converts to
dot decimals.

## Weekly update - step by step

1. **Edit the JSONs** (or have the user supply the new table; apply
   EN+DE to BOTH locations). Update `week_label` (KW34), `date`
   (format `17.08.26 - 21.08.26`), dish titles/descriptions, allergen
   codes. Prices only in `srh-menu.json`; KK daily box in `kk-menu.json`.
2. **Render:** `python3 render.py kk && python3 render.py srh`
3. **POS CSVs:** `python3 pos_import.py` - watch for WARNING lines
   (a KK dish with no SRH price match defaults to 9.90; fix if wrong).
4. **Verify in browser** (see below).
5. **Publish:** `git add -A && git commit -m "..." && git push`.
   Pages auto-deploys in ~40-50 s; CDN max-age 600 s - live URLs may
   serve stale content for up to 10 min.

## Verification - acceptance criteria

- Both pages (EN + DE) of both locations render with the new titles/descs.
- **One A4 page each, no overflow:** for every `.page`, measure
  `footer.top - lastBox.bottom` in the DOM - must be positive on all
  four pages. DOM measurement is authoritative.
- SRH sign: vegan 9,90 / meat 10,90. KK sign: no prices. POS CSVs:
  KK 10 items (KK Curry Vegan 9.90 + KK Curry Chicken 10.90 + 8 dishes),
  SRH 8 items. All in category `0. Lunch`, checkout Yes, online No.
- Allergen chips on the sign match the JSON codes.
- `pos_import.py` printed no unexpected WARNINGs.

## Gotchas

- Longer German descriptions wrap to 2 lines and grow the day boxes -
  if a page overflows the footer, tighten `.day` padding and `.item`
  margin in `template.html` (badge flex-centering tolerates shorter
  boxes), re-render, re-measure.
- KK POS prices are matched from SRH **by dish name** - keep the EN
  dish names identical across both JSONs.
- Do NOT re-render `kk-menu.json`'s `daily.pos` onto the sign - the
  sign shows ONE daily box regardless.
- macOS `grep -o` with brace patterns can return empty spuriously;
  confirm with `grep -c` or the file size.
- One-line descs assume the Lato web font; Arial fallback wraps.

## POS import (manual user step, but verify the CSVs)

SumUp import: item names are the EN titles (POS convention), Category
`0. Lunch`, Display at Checkout Yes, Online Store No, tax 7.00 %, unit
`each.each`, inventory tracked from 0, DE description on invoices.
`Item id`/`Variant id` columns are EMPTY - the importer CREATES new
items each week (the POS holds every past week's items in the archive).

## When done

Report: files changed, prices applied, verification results per page,
any WARNINGs or assumptions (e.g. new KK-only dish defaulted to 9.90).
Working tree clean, push succeeded.
