#!/usr/bin/env python3
"""
יוצר את מראות השפה /en ו-/pl מתוך עמודי המקור העבריים.

מה הוא עושה בכל קובץ:
  • lang/dir  →  en/pl + ltr
  • נתיבים למשאבים משותפים (css/ js/ data/ assets/) — מוסיף רמת ../ אחת,
    כי העמוד ירד רמה אחת בעץ. קישורים פנימיים בין עמודים נשארים כמו שהם,
    כי כל אזור שפה הוא עותק מלא של המבנה.
  • מסיר את בורר השפה הישן — inject-langsw.py יזריק אותו מחדש עם
    הנתיבים הנכונים למיקום החדש.
  • התוכן עצמו נשאר עברית; התרגום נעשה בשלב נפרד, קובץ-קובץ.

⚠ אינו דורס קובץ יעד שכבר תורגם, אלא אם מריצים עם --force.

הרצה:  python3 tools/mirror-langs.py [--force] [--only en]
"""
import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGS = {"en": "English", "pl": "Polski"}
SHARED = ("css/", "js/", "data/", "assets/")
TRANSLATED_MARK = "ROOTS-TRANSLATED"


def he_pages():
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT)
        if ".git" in rel.parts or rel.parts[0] in LANGS:
            continue
        yield p, rel


def bump_shared_paths(html: str) -> str:
    """מוסיף ../ לכל הפניה למשאב משותף (בתוך href/src בלבד)."""
    def fix(m):
        attr, quote, path = m.group(1), m.group(2), m.group(3)
        # לדלג על כתובות מוחלטות
        if path.startswith(("http://", "https://", "//", "#", "mailto:", "data:")):
            return m.group(0)
        core = path.lstrip("./")
        prefix = path[: len(path) - len(core)]
        if core.startswith(SHARED):
            return f'{attr}={quote}../{prefix}{core}{quote}'
        return m.group(0)

    return re.sub(r'\b(href|src)=(["\'])([^"\']+)\2', fix, html)


def bump_fetch_paths(html: str) -> str:
    """fetch('data/…') בתוך סקריפטים משובצים."""
    return re.sub(r"(['\"])(\.{0,2}/?)(data/[^'\"]+)\1", r"\1../\3\1", html)


def strip_langsw(html: str) -> str:
    return re.sub(
        r'[ \t]*<!-- ROOTS-LANGSW -->\s*<div class="langsw".*?</div>\s*',
        "", html, flags=re.S)


def convert(html: str, lang: str) -> str:
    html = re.sub(r'<html[^>]*>', f'<html lang="{lang}" dir="ltr">', html, count=1)
    html = strip_langsw(html)
    html = bump_shared_paths(html)
    html = bump_fetch_paths(html)
    html = html.replace("<head>", f"<head>\n<!-- {TRANSLATED_MARK}: pending -->", 1)
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", choices=list(LANGS))
    a = ap.parse_args()
    langs = [a.only] if a.only else list(LANGS)

    made, kept = 0, 0
    for src, rel in he_pages():
        for lang in langs:
            dst = ROOT / lang / rel
            if dst.exists() and not a.force:
                # לא לדרוס תרגום קיים
                if TRANSLATED_MARK + ": done" in dst.read_text(encoding="utf-8"):
                    kept += 1
                    continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(convert(src.read_text(encoding="utf-8"), lang), encoding="utf-8")
            made += 1

    print(f"mirrored {made} page(s); kept {kept} already-translated page(s)")
    print("→ now run: python3 tools/inject-langsw.py")


if __name__ == "__main__":
    main()
