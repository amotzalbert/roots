#!/usr/bin/env python3
"""
מזריק בורר שפה (עב / EN / PL) לתוך .navlinks בכל עמוד באתר, בכל שלוש
השפות, עם נתיבים יחסיים נכונים לפי עומק העמוד ולפי שפת העמוד.

מבנה האתר:
    /                עברית (ברירת המחדל — לא משנים כתובות קיימות)
    /en/…            אנגלית
    /pl/…            פולנית

אידמפוטנטי: מזהה ROOTS-LANGSW ולא מכפיל.
הרצה:  python3 tools/inject-langsw.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARK = "ROOTS-LANGSW"
LANGS = [("he", "עב"), ("en", "EN"), ("pl", "PL")]


def page_lang_and_key(rel: Path):
    """מחזיר (שפת העמוד, המפתח = הנתיב בתוך אזור השפה)."""
    parts = rel.parts
    if parts and parts[0] in ("en", "pl"):
        return parts[0], Path(*parts[1:])
    return "he", rel


def href_to(from_rel: Path, target_lang: str, key: Path) -> str:
    """נתיב יחסי מהעמוד הנוכחי אל אותו עמוד בשפת היעד."""
    target = key if target_lang == "he" else Path(target_lang) / key
    up = ".." if False else None  # noqa
    # מספר הרמות לעלות = עומק התיקייה של העמוד הנוכחי
    depth = len(from_rel.parts) - 1
    prefix = "../" * depth
    return prefix + target.as_posix()


def build(from_rel: Path, cur_lang: str, key: Path) -> str:
    items = []
    for code, label in LANGS:
        href = href_to(from_rel, code, key)
        cur = ' aria-current="true"' if code == cur_lang else ""
        items.append(f'<a href="{href}" hreflang="{code}" lang="{code}"{cur}>{label}</a>')
    return (
        f'    <!-- {MARK} -->\n'
        f'    <div class="langsw" role="group" aria-label="Language">\n'
        f'      ' + "\n      ".join(items) + "\n"
        f'    </div>\n'
    )


def main():
    pages = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)
    done, skipped = 0, []
    for p in pages:
        html = p.read_text(encoding="utf-8")
        if MARK in html:
            skipped.append((p, "already"))
            continue
        rel = p.relative_to(ROOT)
        lang, key = page_lang_and_key(rel)
        block = build(rel, lang, key)

        # להזריק לפני כפתור הערכה שבתוך .navlinks
        m = re.search(r'[ \t]*<button class="iconbtn" id="theme"', html)
        if not m:
            skipped.append((p, "no theme button"))
            continue
        html = html[: m.start()] + block + html[m.start():]
        p.write_text(html, encoding="utf-8")
        done += 1

    print(f"langsw injected: {done}")
    for p, why in skipped:
        print("  – skipped", p.relative_to(ROOT), f"({why})")


if __name__ == "__main__":
    main()
