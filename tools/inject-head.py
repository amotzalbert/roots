#!/usr/bin/env python3
"""
מזריק ל-<head> של כל עמודי האתר סקריפט משובץ קצר שקובע את ערכת הצבע
לפני הציור הראשון. בלעדיו הדף נצבע לפי העדפת מערכת ההפעלה ורק אז
ui.js (שיושב בסוף ה-body) מחליף אותה — וזה ההבהוב שנראה בכל מעבר עמוד.

אידמפוטנטי: מזהה את הסימון ROOTS-THEME-BOOT ולא מכפיל.
הרצה:  python3 tools/inject-head.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARK = "ROOTS-THEME-BOOT"

SNIPPET = """<!-- ROOTS-THEME-BOOT: must stay inline and before the stylesheet -->
<script>(function(){try{var v=localStorage.getItem('roots-theme');
if(v==='light'||v==='dark')document.documentElement.setAttribute('data-theme',v);}catch(e){}})();</script>
"""


def main():
    pages = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)
    done, skipped = [], []
    for p in pages:
        html = p.read_text(encoding="utf-8")
        if MARK in html:
            skipped.append(p)
            continue
        # להזריק מיד לפני ה-<link> הראשון של גיליון הסגנון
        m = re.search(r'[ \t]*<link[^>]+rel=["\']stylesheet["\'][^>]*>', html)
        if not m:
            skipped.append(p)
            continue
        html = html[: m.start()] + SNIPPET + html[m.start():]
        p.write_text(html, encoding="utf-8")
        done.append(p)

    for p in done:
        print("  ✔", p.relative_to(ROOT))
    for p in skipped:
        print("  – skipped:", p.relative_to(ROOT))
    print(f"\ninjected {len(done)} / skipped {len(skipped)}")


if __name__ == "__main__":
    main()
