#!/usr/bin/env python3
"""Generate SumUp POS import CSVs for both locations (stdlib only).

Weekly workflow: after editing kk-menu.json / srh-menu.json and running
render.py, run:  python3 pos_import.py
Writes kk-pos-import.csv and srh-pos-import.csv to this folder. Commit and
push -- same repo as the menu HTML.

Conventions follow the current SumUp items export:
- Category "0. Lunch", display at checkout Yes, online store No
- Tax 7.00 %, unit each.each, inventory tracked from 0
- Price: SRH from srh-menu.json; KK matched by dish name from srh-menu.json
  (KK sign shows no prices), daily curry defaults to 9.90
- Item id / Variant id left empty -> import creates new items
- Description = German menu text (shows on invoices)
"""
import csv
import io
import json
import pathlib

ROOT = pathlib.Path(__file__).parent

HEADER = [
    "Item name", "Variations", "Option set 1", "Option 1", "Option set 2",
    "Option 2", "Option set 3", "Option 3", "Option set 4", "Option 4",
    "Is variation visible? (Yes/No)", "Price", "Cost price",
    "Variable price? (Yes/No)", "Tax rate (%)", "On sale in Online Store?",
    "Regular price (before sale)", "Set up different prices and VAT for takeaway",
    "Takeaway price", "Takeaway tax rate", "Unit", "Track inventory? (Yes/No)",
    "Quantity", "Low stock threshold", "SKU", "Barcode", "Modifiers",
    "Description (Online Store and Invoices only)", "Category",
    "Display item at Checkout? (Yes/No)", "Display colour in POS checkout",
    "Image 1", "Image 2", "Image 3", "Image 4", "Image 5", "Image 6", "Image 7",
    "Display item in Online Store? (Yes/No)", "SEO title (Online Store only)",
    "SEO description (Online Store only)", "Shipping weight [kg] (Online Store only)",
    "Display service in Bookings? (Yes/No)", "Duration [minutes] (Bookings only)",
    "Location [business/customer] (Bookings only)", "Item id (Do not change)",
    "Variant id (Do not change)",
]

CATEGORY = "0. Lunch"
DAILY_PRICE = "9.90"  # KK daily curry, vegan base


def price_num(price):
    """'9,90 €' -> '9.90' (SumUp CSV uses dot decimals)."""
    return price.replace(" €", "").replace(",", ".")


def item_row(name, desc, price):
    row = [""] * len(HEADER)
    row[0] = name
    row[10] = "Yes"
    row[11] = price
    row[13] = "No"
    row[14] = "7.00"
    row[15] = "No"
    row[17] = "No"
    row[20] = "each.each"
    row[21] = "Yes"
    row[22] = "0"
    row[23] = "0"
    row[27] = desc
    row[28] = CATEGORY
    row[29] = "Yes"
    row[38] = "No"
    row[39] = name
    row[42] = "No"
    return row


def build(location):
    data = json.loads((ROOT / ("%s-menu.json" % location)).read_text(encoding="utf-8"))
    srh = json.loads((ROOT / "srh-menu.json").read_text(encoding="utf-8"))
    srh_prices = {}
    for day in srh["days"]:
        for it in day["items"]:
            srh_prices[it["name_en"]] = price_num(it["price"])

    rows = []
    if location == "kk" and "daily" in data:
        daily = data["daily"]
        if "pos" in daily:
            for pi in daily["pos"]:
                rows.append(item_row(pi["name"],
                                     pi.get("desc", daily["desc_de"]),
                                     price_num(pi["price"])))
        else:
            desc = daily["desc_de"] + " " + daily["note_de"]
            rows.append(item_row(daily["name_en"], desc, DAILY_PRICE))

    for day in data["days"]:
        for it in day["items"]:
            price = srh_prices.get(it["name_en"])
            if price is None:
                print("WARNING %s: no SRH price for %r, defaulting to 9.90"
                      % (location, it["name_en"]))
                price = DAILY_PRICE
            rows.append(item_row(it["name_en"], it["desc_de"], price))

    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(HEADER)
    w.writerows(rows)
    out = ROOT / ("%s-pos-import.csv" % location)
    out.write_text(buf.getvalue(), encoding="utf-8")
    print(out.name, "written:", len(rows), "items,", out.stat().st_size, "bytes")


def main():
    for location in ("kk", "srh"):
        build(location)


if __name__ == "__main__":
    main()
