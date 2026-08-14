#!/usr/bin/env python3
"""
מזריק את אשכול הפקדים הצף (בורר שפה בדגלים + ערכה + גופן) לפני </body>
בכל עמוד באתר, בכל שלוש השפות, עם נתיבים יחסיים נכונים לפי עומק העמוד
ולפי שפת העמוד.

מאז 15.8.2026 הפקדים אינם יושבים ב-.navlinks אלא באשכול קבוע
<div class="ctrl"> בפינת המסך (CSS: ‎.ctrl ב-main.css). בורר השפה מציג
דגלים (ישראל/בריטניה/פולין) במקום אותיות. עמוד שכבר יש בו את הכפתורים
בתוך ה-navlinks — יש להסירם ידנית או בעזרת הסקריפט ההיסטורי; הכלי הזה
רק מוסיף אשכול חדש לעמוד שאין בו ROOTS-LANGSW.

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

FLAGS = {
    "he": ('<svg viewBox="0 0 21 15" aria-hidden="true"><rect width="21" height="15" fill="#fff"/>'
           '<rect y="1.6" width="21" height="1.9" fill="#0038b8"/><rect y="11.5" width="21" height="1.9" fill="#0038b8"/>'
           '<path d="M10.5 4.6 12.9 8.75H8.1Z M10.5 10.4 8.1 6.25h4.8Z" fill="none" stroke="#0038b8" stroke-width=".75"/></svg>'),
    "en": ('<svg viewBox="0 0 60 30" aria-hidden="true"><rect width="60" height="30" fill="#012169"/>'
           '<path d="M0 0 60 30M60 0 0 30" stroke="#fff" stroke-width="6"/>'
           '<path d="M0 0 60 30M60 0 0 30" stroke="#C8102E" stroke-width="2.4"/>'
           '<path d="M30 0v30M0 15h60" stroke="#fff" stroke-width="10"/>'
           '<path d="M30 0v30M0 15h60" stroke="#C8102E" stroke-width="6"/></svg>'),
    "pl": ('<svg viewBox="0 0 21 15" aria-hidden="true"><rect width="21" height="15" fill="#fff"/>'
           '<rect y="7.5" width="21" height="7.5" fill="#dc143c"/></svg>'),
}
NAMES = {"he": "עברית", "en": "English", "pl": "Polski"}
GROUP_LABEL = {"he": "שפה ותצוגה", "en": "Language and display", "pl": "Język i wyświetlanie"}
THEME_TITLE = {"he": "מצב תצוגה", "en": "Colour theme", "pl": "Motyw kolorów"}
BIG_TITLE = {"he": "הגדלת גופן", "en": "Larger text", "pl": "Większy tekst"}
BIG_LABEL = {"he": "א+", "en": "A+", "pl": "A+"}


def page_lang_and_key(rel: Path):
    """מחזיר (שפת העמוד, המפתח = הנתיב בתוך אזור השפה)."""
    parts = rel.parts
    if parts and parts[0] in ("en", "pl"):
        return parts[0], Path(*parts[1:])
    return "he", rel


def href_to(from_rel: Path, target_lang: str, key: Path) -> str:
    """נתיב יחסי מהעמוד הנוכחי אל אותו עמוד בשפת היעד."""
    target = key if target_lang == "he" else Path(target_lang) / key
    depth = len(from_rel.parts) - 1
    prefix = "../" * depth
    return prefix + target.as_posix()


def build(from_rel: Path, cur_lang: str, key: Path) -> str:
    items = []
    for code in ("he", "en", "pl"):
        href = href_to(from_rel, code, key)
        cur = ' aria-current="true"' if code == cur_lang else ""
        items.append(
            f'    <a href="{href}" hreflang="{code}" lang="{code}" '
            f'title="{NAMES[code]}" aria-label="{NAMES[code]}"{cur}>{FLAGS[code]}</a>'
        )
    return (
        f'<!-- {MARK} -->\n'
        f'<div class="ctrl" role="group" aria-label="{GROUP_LABEL[cur_lang]}">\n'
        f'  <div class="langsw" role="group" aria-label="Language">\n'
        + "\n".join(items) + "\n"
        f'  </div>\n'
        f'  <button class="iconbtn" id="theme" title="{THEME_TITLE[cur_lang]}">◐</button>\n'
        f'  <button class="iconbtn" id="bigfont" title="{BIG_TITLE[cur_lang]}">{BIG_LABEL[cur_lang]}</button>\n'
        f'</div>\n'
    )


def main():
    pages = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)
    done, skipped = 0, []
    for p in pages:
        html = p.read_text(encoding="utf-8")
        if MARK in html or 'class="ctrl"' in html:
            # ‎class="ctrl"‎ בלי MARK = עמוד עברי־בלבד (כמו research.html) שקיבל
            # אשכול פקדים בלי בורר שפה — אין להזריק לו בורר.
            skipped.append((p, "already"))
            continue
        rel = p.relative_to(ROOT)
        lang, key = page_lang_and_key(rel)
        block = build(rel, lang, key)

        if "</body>" not in html:
            skipped.append((p, "no </body>"))
            continue
        # אם נשארו כפתורי theme/bigfont ישנים בתוך ה-navlinks — לא נוגעים בהם,
        # רק מתריעים; העמוד יקבל את האשכול החדש והישנים יוסרו ידנית.
        if re.search(r'navlinks[\s\S]{0,600}id="theme"', html):
            skipped.append((p, "old buttons still in navlinks — remove them first"))
            continue
        html = html.replace("</body>", block + "</body>", 1)
        p.write_text(html, encoding="utf-8")
        done += 1

    print(f"ctrl cluster injected: {done}")
    for p, why in skipped:
        print("  – skipped", p.relative_to(ROOT), f"({why})")


if __name__ == "__main__":
    main()
