#!/usr/bin/env python3
"""
ged2json.py — ממיר את albert-rywenbajrych.ged למודל הנתונים של אתר «שורשים».

פלט: site/data/people.albert.json · unions.albert.json · sources.albert.json
הסכמה מוגדרת ב-SITE-PLAN.md §4.

⚠ מדיניות פרטיות: לפי הכרעת G1 (8.8.2026) האתר פומבי כולל פרטי אנשים חיים.
   הדגל living נשמר בכל זאת, כדי שאפשר יהיה לשנות מדיניות בלי לבנות מחדש.
"""
import re, json, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # ~/Projects/family-history
GED  = ROOT / "albert" / "chart" / "albert-rywenbajrych.ged"
OUT  = ROOT / "site" / "data"

# ── דירוג ודאות: מתוך נוסח ההערות ב-GEDCOM ──────────────────────────────
GRADE_PATTERNS = [
    (r'\(documented',  "documented"),   # ● אקט/מסמך שנקרא
    (r'\(probable',    "probable"),     # ◐ אינדקס או הצלבה חזקה
    (r'\(inference',   "inference"),    # ○ הסקה בלבד
]

def grade_of(text: str) -> str | None:
    low = (text or "").lower()
    for pat, g in GRADE_PATTERNS:
        if re.search(pat, low):
            return g
    return None


def parse_gedcom(raw: str):
    """מפרק ל-records; כל record הוא עץ של (level, tag, value, children)."""
    lines = []
    for ln in raw.splitlines():
        if not ln.strip():                # שורה ריקה — הפרדה בין רשומות, לא המשך
            continue
        m = re.match(r'^(\d+)\s+(?:(@[^@]+@)\s+)?(\w+)(?:\s(.*))?$', ln)
        if m:
            lvl, xref, tag, val = m.groups()
            lines.append([int(lvl), xref, tag, val or ""])
        elif lines:                       # שורת המשך שבורה — לצרף לקודמת
            lines[-1][3] += " " + ln.strip()

    # CONT/CONC → מיזוג לערך של השורה שמעליהן
    merged = []
    for lvl, xref, tag, val in lines:
        if tag == "CONT" and merged:
            merged[-1][3] += "\n" + val
        elif tag == "CONC" and merged:
            merged[-1][3] += val
        else:
            merged.append([lvl, xref, tag, val])

    def build(idx, level):
        node = {"tag": merged[idx][2], "xref": merged[idx][1],
                "value": merged[idx][3], "children": []}
        i = idx + 1
        while i < len(merged) and merged[i][0] > level:
            if merged[i][0] == level + 1:
                child, i = build(i, level + 1)
                node["children"].append(child)
            else:
                i += 1
        return node, i

    records, i = [], 0
    while i < len(merged):
        if merged[i][0] == 0:
            rec, i = build(i, 0)
            records.append(rec)
        else:
            i += 1
    return records


def kids(node, tag):
    return [c for c in node["children"] if c["tag"] == tag]

XREF_RE = re.compile(r'@([^@\s]+)@')

def source_ids(node):
    """מזהי מקור מתוך תגי SOUR — עמיד לרווחים ולזבל בסוף השורה."""
    out = []
    for c in kids(node, "SOUR"):
        m = XREF_RE.search(c["value"] or "")
        if m:
            out.append("s-" + m.group(1).lower())
    return out

def first(node, tag, default=""):
    k = kids(node, tag)
    return k[0]["value"] if k else default

def notes(node):
    return [c["value"] for c in kids(node, "NOTE")]


def event(node, tag):
    """BIRT/DEAT/MARR → dict עם תאריך, מקום, דירוג ומקורות."""
    k = kids(node, tag)
    if not k:
        return None
    e = k[0]
    date  = first(e, "DATE")
    place = first(e, "PLAC")
    ns    = notes(e)
    g     = next((grade_of(n) for n in ns if grade_of(n)), None)
    ev = {}
    if date:  ev["date"] = date
    if place: ev["place"] = place
    if g:     ev["grade"] = g
    if ns:    ev["notes"] = ns
    srcs = source_ids(e)
    if srcs: ev["sources"] = srcs
    return ev or None


def slugify(name: str) -> str:
    s = re.sub(r'[^a-zA-Z0-9]+', '-', name).strip('-').lower()
    return s or "unknown"


def main():
    raw = GED.read_text(encoding="utf-8")
    records = parse_gedcom(raw)

    people, unions, sources = {}, [], {}
    id_map = {}   # @I1@ → p-slug

    # ── SOUR ────────────────────────────────────────────────────────────
    for r in records:
        if r["tag"] != "SOUR" or not r["xref"]:
            continue
        xid = r["xref"].strip("@")
        sources["s-" + xid.lower()] = {
            "id": "s-" + xid.lower(),
            "gedcomId": xid,
            "title": first(r, "TITL"),
            "author": first(r, "AUTH"),
            "publication": first(r, "PUBL"),
            "repository": first(r, "REPO"),
            "citation": first(r, "PAGE"),
            "notes": notes(r),
        }

    # ── INDI ────────────────────────────────────────────────────────────
    for r in records:
        if r["tag"] != "INDI" or not r["xref"]:
            continue
        xid = r["xref"].strip("@")
        nm  = first(r, "NAME")
        given = surname = ""
        nk = kids(r, "NAME")
        if nk:
            given   = first(nk[0], "GIVN") or (nm.split("/")[0].strip() if nm else "")
            surname = first(nk[0], "SURN")
            if not surname and "/" in nm:
                surname = nm.split("/")[1]
        latin = " ".join(x for x in (given, surname) if x).strip()
        pid = "p-" + slugify(latin or xid)
        while pid in people:                       # התנגשות שמות זהים
            pid += "-" + xid.lower()
        id_map["@" + xid + "@"] = pid

        ns = notes(r)
        birth, death = event(r, "BIRT"), event(r, "DEAT")
        # אדם נחשב חי אם אין לו רשומת פטירה ואין לו תאריך לידה (מדיניות ה-GEDCOM המקורית)
        living = death is None and (birth is None or not birth.get("date"))

        people[pid] = {
            "id": pid,
            "branch": "albert",
            "gedcomId": xid,
            "names": {"he": "", "latin": latin, "given": given, "surname": surname,
                      "variants": []},
            "sex": first(r, "SEX"),
            "living": living,
            "birth": birth,
            "death": death,
            "occupation": first(r, "OCCU"),
            "notes": ns,
            "grade": next((grade_of(n) for n in ns if grade_of(n)), None),
            "sources": source_ids(r),
            "photos": [], "docs": [], "bioChapter": None,
            "_fams": [c["value"] for c in kids(r, "FAMS")],
            "_famc": [c["value"] for c in kids(r, "FAMC")],
        }

    # ── FAM ─────────────────────────────────────────────────────────────
    for r in records:
        if r["tag"] != "FAM" or not r["xref"]:
            continue
        xid = r["xref"].strip("@")
        husb = id_map.get(first(r, "HUSB"))
        wife = id_map.get(first(r, "WIFE"))
        children = [id_map[c["value"]] for c in kids(r, "CHIL") if c["value"] in id_map]
        u = {
            "id": "u-" + xid.lower(),
            "branch": "albert",
            "gedcomId": xid,
            "spouses": [s for s in (husb, wife) if s],
            "children": children,
            "marriage": event(r, "MARR"),
            "notes": notes(r),
        }
        unions.append(u)

    # ניקוי שדות עזר
    for p in people.values():
        p.pop("_fams", None); p.pop("_famc", None)
        p["sources"] = [s for s in p["sources"] if s]

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "people.albert.json").write_text(
        json.dumps(list(people.values()), ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "unions.albert.json").write_text(
        json.dumps(unions, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "sources.albert.json").write_text(
        json.dumps(list(sources.values()), ensure_ascii=False, indent=1), encoding="utf-8")

    graded = sum(1 for p in people.values() if p.get("grade"))
    print(f"people   : {len(people)}  (מהם עם דירוג: {graded})")
    print(f"unions   : {len(unions)}")
    print(f"sources  : {len(sources)}")
    print(f"living   : {sum(1 for p in people.values() if p['living'])}")
    print(f"→ {OUT}")

if __name__ == "__main__":
    main()
