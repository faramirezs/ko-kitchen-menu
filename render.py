#!/usr/bin/env python3
"""Render menu.html from menu.json + template.html (stdlib only).

Weekly workflow: edit menu.json (or tell the assistant what changed),
then run:  python3 render.py
Commit the generated menu.html and push -- GitHub Pages serves it.
"""
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).parent

# Allergen letter -> tooltip title per language (LMIV 1169/2011 codes).
ALLERGEN_TITLES = {
    "en": {
        "A": "Cereals containing gluten",
        "B": "Crustaceans",
        "C": "Eggs",
        "D": "Fish",
        "E": "Peanuts",
        "F": "Soybeans",
        "G": "Milk",
        "H": "Nuts",
        "L": "Celery",
        "M": "Mustard",
        "N": "Sesame",
        "O": "Sulphur dioxide/Sulphites",
        "P": "Lupin",
    },
    "de": {
        "A": "Glutenhaltiges Getreide",
        "B": "Krebstiere",
        "C": "Eier",
        "D": "Fische",
        "E": "Erdnüsse",
        "F": "Sojabohnen",
        "G": "Milch",
        "H": "Schalenfrüchte",
        "L": "Sellerie",
        "M": "Senf",
        "N": "Sesam",
        "O": "Schwefeldioxid/Sulfite",
        "P": "Lupinen",
    },
}

TODO_TITLES = {
    "en": "Please add allergen codes",
    "de": "Allergene bitte ergänzen",
}

BADGES = (
    '      <div class="badge vegan">'
    '<svg class="leaf" viewBox="0 0 24 24" aria-hidden="true">'
    '<path fill="currentColor" d="M11 12.5C6 12.5 2.8 9.3 2.8 3.2 8.2 3.2 11 6.5 11 12.5z"/>'
    '<path fill="currentColor" d="M13 12.5c5 0 8.2-3.2 8.2-9.3-5.4 0-8.2 3.3-8.2 9.3z"/>'
    '<path d="M12 13v8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" fill="none"/>'
    '</svg><span>VEGAN</span></div>\n'
    '      <div class="badge halal"><span>HALAL</span></div>'
)


def chips(lang, codes):
    """Allergen chips for one dish. Empty list -> red '?' todo chip."""
    titles = ALLERGEN_TITLES[lang]
    if not codes:
        return '<span class="alg todo" title="%s">?</span>' % TODO_TITLES[lang]
    return "".join('<span class="alg" title="%s">%s</span>' % (titles[c], c) for c in codes)


def item_html(lang, item):
    label = "Allergens" if lang == "en" else "Allergene"
    name = html.escape(item["name_" + lang])
    desc = html.escape(item["desc_" + lang])
    return (
        '      <div class="item">\n'
        '        <div class="name" contenteditable="true">%s</div>\n'
        '        <div class="desc" contenteditable="true">%s</div>\n'
        '        <div class="alg-row"><span class="alg-label">%s</span>%s</div>\n'
        "      </div>"
    ) % (name, desc, label, chips(lang, item["allergens"]))


def day_html(lang, day):
    items = "\n".join(item_html(lang, item) for item in day["items"])
    return (
        "    <article class=\"day\">\n"
        "      <div class=\"day-title\" contenteditable=\"true\">%s</div>\n"
        "%s\n"
        "%s\n"
        "    </article>"
    ) % (day["title_" + lang], items, BADGES)


def main():
    data = json.loads((ROOT / "menu.json").read_text(encoding="utf-8"))
    template = (ROOT / "template.html").read_text(encoding="utf-8")

    days_en = "\n".join(day_html("en", d) for d in data["days"])
    days_de = "\n".join(day_html("de", d) for d in data["days"])

    html = (
        template.replace("{{WEEK}}", data["week_label"])
        .replace("{{DATE}}", data["date"])
        .replace("{{KW_DL}}", data["kw"])
        .replace("{{DAYS_EN}}", days_en)
        .replace("{{DAYS_DE}}", days_de)
    )

    # Safety: every placeholder must be consumed.
    leftovers = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if leftovers:
        raise SystemExit("Unconsumed placeholders: %s" % sorted(set(leftovers)))

    (ROOT / "menu.html").write_text(html, encoding="utf-8")
    print("menu.html written:", (ROOT / "menu.html").stat().st_size, "bytes")


if __name__ == "__main__":
    main()
