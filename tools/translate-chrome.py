#!/usr/bin/env python3
"""
מתרגם את ה"שלד" החוזר של האתר — סרגל ניווט, כפתורים, כותרת תחתונה —
בכל עמודי /en ו-/pl. אלה מחרוזות קבועות שחוזרות ב-66 מקומות, ולכן
נכון לתרגם אותן מכנית ולא ידנית.

⚠ אידמפוטנטי: מחליף רק אם המחרוזת העברית עדיין שם. אפשר להריץ שוב
   אחרי שסוכני התרגום סיימו, בלי לשבור את עבודתם.

הרצה:  python3 tools/translate-chrome.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (עברית, אנגלית, פולנית) — מחרוזות שלד בלבד
CHROME = [
    # מותג וניווט ראשי
    ("שורשים",             "Roots",        "Korzenie"),
    ("מוסקל–שאפיר",        "Moskal–Schafir", "Moskal–Szafir"),
    ("אלברט–ריבנבייריך",   "Albert–Rywenbajrych", "Albert–Rywenbajrych"),
    (">אילן<",             ">Family tree<", ">Drzewo<"),
    (">מפה<",              ">Map<",        ">Mapa<"),
    (">מסמכים<",           ">Documents<",  ">Dokumenty<"),
    (">מקורות<",           ">Sources<",    ">Źródła<"),
    (">חיפוש<",            ">Search<",     ">Szukaj<"),
    # כפתורים
    ('title="מצב תצוגה"',  'title="Colour theme"', 'title="Motyw kolorów"'),
    ('title="הגדלת גופן"', 'title="Larger text"',  'title="Większy tekst"'),
    (">א+<",               ">A+<",         ">A+<"),
    # כותרת תחתונה
    ("שורשים · תולדות משפחות מוסקל–שאפיר ואלברט–ריבנבייריך · כל התאריכים המסומנים \"בערך\" הם הערכה, לא תיעוד",
     "Roots · A history of the Moskal–Schafir and Albert–Rywenbajrych families · Any date marked “about” is an estimate, not a record",
     "Korzenie · Historia rodzin Moskal–Szafir i Albert–Rywenbajrych · Każda data oznaczona „ok.” jest szacunkiem, nie zapisem"),
    ("שורשים · תולדות משפחות מוסקל–שאפיר ואלברט–ריבנבייריך",
     "Roots · A history of the Moskal–Schafir and Albert–Rywenbajrych families",
     "Korzenie · Historia rodzin Moskal–Szafir i Albert–Rywenbajrych"),
]

IDX = {"en": 1, "pl": 2}


def main():
    total = 0
    for lang, col in IDX.items():
        base = ROOT / lang
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.html")):
            html = p.read_text(encoding="utf-8")
            before = html
            for row in sorted(CHROME, key=lambda r: -len(r[0])):
                he, tgt = row[0], row[col]
                if he in html:
                    html = html.replace(he, tgt)
            if html != before:
                p.write_text(html, encoding="utf-8")
                total += 1
    print(f"chrome translated in {total} page(s)")


if __name__ == "__main__":
    main()
