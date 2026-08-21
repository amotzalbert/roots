#!/usr/bin/env python3
"""
מחלץ את בלוקי ה-<style> הפנימיים מכל עמודי האתר אל css/pages/ משותפים
לשלוש השפות.

למה: הבלוק הפנימי משוכפל שלוש פעמים (he/en/pl), ובעותקי en/pl הוא יושב
בתוך קבצים המסומנים «ROOTS-TRANSLATED: done» — כלומר כל שינוי עיצוב נאלץ
לגעת בקבצים המתורגמים. אחרי החילוץ העיצוב חי ב-css/ בלבד, ואף עמוד מתורגם
אינו מחזיק בו.

הרצה:  python3 tools/extract-page-css.py [--check] [--stamp 20260821a]
       --check  מריץ אימות בלבד, בלי לכתוב דבר.

הסקריפט אידמפוטנטי: הרצה חוזרת על עץ שכבר הומר אינה עושה דבר.
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGS = ("en", "pl")
CSS_PAGES = ROOT / "css" / "pages"

STYLE_RE = re.compile(r"[ \t]*<style>\n(.*?)\n[ \t]*</style>\n", re.S)
MAIN_RE = re.compile(r'([ \t]*<link rel="stylesheet" href=")((?:\.\./)*)(css/main\.css[^"]*)(">\n)')


def he_pages():
    """כל עמודי המקור העבריים, כפי ש-mirror-langs.py מגדיר אותם."""
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT)
        if ".git" in rel.parts or "worktrees" in rel.parts or rel.parts[0] in LANGS:
            continue
        yield rel


def sheet_name(rel: Path) -> str:
    """moskal-szafir/ch-beit-moskal.html → moskal-szafir-ch-beit-moskal.css"""
    if rel.as_posix() == "index.html":
        return "home.css"
    return rel.with_suffix("").as_posix().replace("/", "-") + ".css"


def copies(rel: Path):
    """שלושת העותקים של אותו עמוד — עברית, אנגלית, פולנית."""
    yield ROOT / rel
    for lang in LANGS:
        yield ROOT / lang / rel


def split_head_body(html: str):
    i = html.find("<body")
    return (html, "") if i < 0 else (html[:i], html[i:])


def body_hash(html: str) -> str:
    return hashlib.sha256(split_head_body(html)[1].encode()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="אימות בלבד, בלי כתיבה")
    ap.add_argument("--stamp", default="20260821a", help="חותם גרסה ל-cache busting")
    args = ap.parse_args()

    pages = list(he_pages())
    problems: list[str] = []
    warnings: list[str] = []
    work: list[tuple[Path, str, str]] = []  # (rel, sheet, css)

    # ── שלב 1: אימות ההנחה שהבלוקים זהים בשלוש השפות ──────────────
    for rel in pages:
        blocks, missing = {}, []
        for path in copies(rel):
            if not path.exists():
                missing.append(path.relative_to(ROOT).as_posix())
                continue
            m = STYLE_RE.search(path.read_text(encoding="utf-8"))
            blocks[path.relative_to(ROOT).as_posix()] = m.group(1) if m else None

        present = {k: v for k, v in blocks.items() if v is not None}
        if not present:
            continue  # אין בלוק פנימי — או שכבר חולץ. אין מה לעשות.

        if len(present) != len(blocks):
            no_block = sorted(set(blocks) - set(present))
            problems.append(f"{rel}: בלוק <style> קיים רק בחלק מהעותקים; חסר ב-{no_block}")
            continue
        if missing:
            # עמוד שטרם מוראה לכל השפות (למשל research-index) — לא שגיאה.
            warnings.append(f"{rel}: קיים רק ב-{len(present)} שפות; חסר: {missing}")
        if len({hashlib.sha256(v.encode()).hexdigest() for v in present.values()}) != 1:
            problems.append(f"{rel}: בלוקי ה-<style> נבדלים בין השפות — נדרשת הכרעה אנושית")
            continue

        work.append((rel, sheet_name(rel), next(iter(present.values()))))

    if problems:
        print("✗ אימות נכשל — לא נכתב דבר:\n", file=sys.stderr)
        for p in problems:
            print(f"  · {p}", file=sys.stderr)
        return 1

    if not work:
        print("✓ אין מה לחלץ — העץ כבר מומר. (no-op)")
        return 0

    print(f"✓ אימות עבר: {len(work)} עמודים, בלוקים זהים בכל שפה שקיימת.")
    for w in warnings:
        print(f"  ⚠ {w}")
    if args.check:
        for rel, sheet, css in work:
            print(f"  {rel}  →  css/pages/{sheet}  ({len(css.splitlines())} שורות)")
        return 0

    # ── שלב 2: כתיבת גיליונות הסגנון ──────────────────────────────
    CSS_PAGES.mkdir(parents=True, exist_ok=True)
    for rel, sheet, css in work:
        (CSS_PAGES / sheet).write_text(
            f"/* ═══ {rel.as_posix()} ═══ חולץ מהבלוק הפנימי, משותף ל-he/en/pl ═══ */\n{css}\n",
            encoding="utf-8",
        )

    # ── שלב 3: החלפת הבלוק בקישור, בכל 70 הקבצים ──────────────────
    changed = 0
    for rel, sheet, _ in work:
        for path in copies(rel):
            if not path.exists():
                continue
            html = path.read_text(encoding="utf-8")
            before = body_hash(html)

            m = MAIN_RE.search(html)
            if not m:
                print(f"✗ {path.relative_to(ROOT)}: לא נמצא קישור ל-main.css", file=sys.stderr)
                return 1
            prefix = m.group(2)  # אותה רמת ../ בדיוק כמו main.css

            link = f'{m.group(1)}{prefix}css/pages/{sheet}?v={args.stamp}{m.group(4)}'
            out = STYLE_RE.sub("", html, count=1)
            out = out[: m.end()] + link + out[m.end():]

            if body_hash(out) != before:
                print(f"✗ {path.relative_to(ROOT)}: ה-<body> השתנה — בוטל", file=sys.stderr)
                return 1

            path.write_text(out, encoding="utf-8")
            changed += 1

    print(f"✓ {changed} קבצים עודכנו · {len(work)} גיליונות ב-css/pages/")
    print("  ה-<body> של כל קובץ אומת כזהה לפני ואחרי.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
