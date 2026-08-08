#!/usr/bin/env python3
"""
build-data.py — מאחד את שני הענפים לקבצי הנתונים שהאתר טוען.

קלט : people.albert.json + he-names.albert.json + people.moskal.json
       unions.albert.json + unions.moskal.json
       sources.albert.json + sources.moskal.json (אם קיים)
       places.json
פלט  : people.json · unions.json · sources.json · index.json (אינדקס חיפוש)

הרצה: python3 build-data.py   (אחרי ged2json.py)
"""
import json, re, unicodedata
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"

def load(name, default=None):
    p = DATA / name
    if not p.exists():
        return default if default is not None else []
    return json.loads(p.read_text(encoding="utf-8"))

def save(name, obj):
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")

# ── מפות עזר ────────────────────────────────────────────────────────────
PLACE_BY_LATIN = {}
def norm_place(value, places):
    """ממיר מחרוזת מקום חופשית מה-GEDCOM למזהה מקום, אם אפשר."""
    if not value:
        return value
    if value.startswith(("pl-", "ua-", "il-")):
        return value
    low = value.lower()
    for pl in places:
        if pl["latin"].lower().split(",")[0] in low or pl["he"] in value:
            return pl["id"]
    return value                      # נשאר כטקסט חופשי — מוצג כמות שהוא

MONTHS = {"JAN":"ינואר","FEB":"פברואר","MAR":"מרץ","APR":"אפריל","MAY":"מאי","JUN":"יוני",
          "JUL":"יולי","AUG":"אוגוסט","SEP":"ספטמבר","OCT":"אוקטובר","NOV":"נובמבר","DEC":"דצמבר"}

def he_date(d):
    """GEDCOM date → עברית קריאה. שומר על ABT/BEF/AFT/BET."""
    if not d:
        return None
    s = d.strip().upper()
    pre = ""
    for tag, heb in (("ABT","בערך "), ("BEF","לפני "), ("AFT","אחרי "), ("EST","בקירוב ")):
        if s.startswith(tag):
            pre, s = heb, s[len(tag):].strip()
    m = re.match(r'^BET\s+(.+?)\s+AND\s+(.+)$', s)
    if m:
        return f"בין {he_date(m.group(1))} ל{he_date(m.group(2))}"
    m = re.match(r'^(\d{1,2})\s+([A-Z]{3})\s+(\d{4})$', s)
    if m:
        return f"{pre}{int(m.group(1))} ב{MONTHS.get(m.group(2), m.group(2))} {m.group(3)}"
    m = re.match(r'^([A-Z]{3})\s+(\d{4})$', s)
    if m:
        return f"{pre}{MONTHS.get(m.group(1), m.group(1))} {m.group(2)}"
    return f"{pre}{s}"

def main():
    places = load("places.json")
    he_map = load("he-names.albert.json", {})

    people = []

    # ── ענף אלברט: החלת שמות עבריים + נרמול מקומות ──────────────────
    for p in load("people.albert.json"):
        ov = he_map.get(p["gedcomId"], {}) if p.get("gedcomId") else {}
        if ov.get("he"):
            p["names"]["he"] = ov["he"]
        # אחרת: לשמר את השם העברי שכבר קיים ברשומה עצמה (אנשים שנוספו ידנית)
        if ov.get("variants"):
            p["names"]["variants"] = ov["variants"]
        if ov.get("note"):
            p.setdefault("notes", []).append(ov["note"])
        for ev in ("birth", "death"):
            if p.get(ev):
                p[ev]["place"] = norm_place(p[ev].get("place"), places)
                p[ev]["dateHe"] = he_date(p[ev].get("date"))
        people.append(p)

    # ── ענף מוסקל ────────────────────────────────────────────────────
    for p in load("people.moskal.json"):
        p.setdefault("gedcomId", None)
        p["names"].setdefault("variants", [])
        for ev in ("birth", "death"):
            if p.get(ev):
                p[ev]["place"] = norm_place(p[ev].get("place"), places)
                p[ev]["dateHe"] = he_date(p[ev].get("date"))
        p.setdefault("occupation", "")
        p.setdefault("notes", [])
        people.append(p)

    unions = load("unions.albert.json") + load("unions.moskal.json")
    for u in unions:
        if u.get("marriage"):
            u["marriage"]["place"] = norm_place(u["marriage"].get("place"), places)
            u["marriage"]["dateHe"] = he_date(u["marriage"].get("date"))

    sources = load("sources.albert.json") + load("sources.moskal.json")

    # ── קשרי הורות דו-כיווניים, לנוחות האילן ─────────────────────────
    by_id = {p["id"]: p for p in people}
    for p in people:
        p["parents"], p["spouses"], p["children"] = [], [], []
    for u in unions:
        for s in u["spouses"]:
            if s in by_id:
                by_id[s]["spouses"] += [x for x in u["spouses"] if x != s]
                by_id[s]["children"] += [c for c in u["children"] if c in by_id]
        for c in u["children"]:
            if c in by_id:
                by_id[c]["parents"] += [s for s in u["spouses"] if s in by_id]
    for p in people:
        for k in ("parents", "spouses", "children"):
            p[k] = list(dict.fromkeys(p[k]))          # ייחוד תוך שמירת סדר

    # ── אינדקס חיפוש ─────────────────────────────────────────────────
    def strip_niqqud(s):
        return "".join(ch for ch in unicodedata.normalize("NFD", s or "")
                       if not (0x0591 <= ord(ch) <= 0x05C7))
    index = []
    for p in people:
        terms = [p["names"]["he"], p["names"]["latin"], *p["names"].get("variants", [])]
        terms.append(strip_niqqud(p["names"]["he"]))
        index.append({"id": p["id"], "type": "person", "branch": p["branch"],
                      "label": p["names"]["he"] or p["names"]["latin"],
                      "sub": p["names"]["latin"],
                      "terms": " ".join(t for t in terms if t)})
    for pl in places:
        index.append({"id": pl["id"], "type": "place", "branch": pl.get("branch", ""),
                      "label": pl["he"], "sub": pl["latin"],
                      "terms": " ".join(str(pl.get(k, "")) for k in
                                        ("he", "latin", "yiddish", "ukrainian", "region"))})

    save("people.json", people)
    save("unions.json", unions)
    save("sources.json", sources)
    save("index.json", index)

    from collections import Counter
    print(f"people : {len(people)}  ({dict(Counter(p['branch'] for p in people))})")
    print(f"unions : {len(unions)}")
    print(f"sources: {len(sources)} · places: {len(places)} · index: {len(index)}")
    miss = [p['id'] for p in people if not p['names']['he']]
    print("ללא שם עברי:", miss or "אין")

if __name__ == "__main__":
    main()
