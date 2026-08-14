#!/usr/bin/env python3
"""
מתרגם את שבעת עמודי הליבה (index, tree, map, documents, sources, search,
methodology) ב-/en וב-/pl. אלה עמודי כלים עם טקסט קצר וקבוע — כולל
מחרוזות בתוך <script> משובץ, שסוכני תרגום אינם אמורים לגעת בהן.

⚠ אידמפוטנטי — מחליף רק אם המחרוזת העברית עדיין קיימת.
הרצה:  python3 tools/translate-core.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (עברית, אנגלית, פולנית)
PAIRS = [
    # ── כותרות עמודים ────────────────────────────────────────────────
    ("<title>חיפוש · ", "<title>Search · ", "<title>Szukaj · "),
    ("<title>נספח מקורות · ", "<title>Sources · ", "<title>Źródła · "),
    ("<title>מסמכים · ", "<title>Documents · ", "<title>Dokumenty · "),
    ("<title>מפת המקומות · ", "<title>Map of places · ", "<title>Mapa miejsc · "),
    ("<title>אילן היוחסין · ", "<title>Family tree · ", "<title>Drzewo genealogiczne · "),
    ("<title>מתודולוגיה · ", "<title>Method · ", "<title>Metodologia · "),
    ("<title>שורשים — תולדות משפחות מוסקל–שאפיר ואלברט–ריבנבייריך</title>",
     "<title>Roots — A history of the Moskal–Schafir and Albert–Rywenbajrych families</title>",
     "<title>Korzenie — Historia rodzin Moskal–Szafir i Albert–Rywenbajrych</title>"),

    # ── index ────────────────────────────────────────────────────────
    ("שני נתיבים משפחתיים: וויסלביצה שבלובלין וורשה–אופטוב, מגובים במסמכי ארכיון, מפות ואילן יוחסין אינטראקטיבי.",
     "Two family routes: Wojsławice in the Lublin region, and Warsaw–Opatów — documented from archive records, with maps and an interactive family tree.",
     "Dwie rodzinne drogi: Wojsławice na Lubelszczyźnie oraz Warszawa–Opatów — udokumentowane aktami archiwalnymi, z mapami i interaktywnym drzewem genealogicznym."),
    ("<p class=\"kicker\">תולדות משפחה</p>",
     "<p class=\"kicker\">A family history</p>",
     "<p class=\"kicker\">Historia rodziny</p>"),
    ("""שני נתיבים אל אותה נקודה: מוויסלביצה שבמחוז לובלין ומוורשה־אופטוב,
       דרך גליציה, ווהלין ודורוהוסק שעל נהר הבוג — עד ישראל.
       כל טענה כאן מגובה במסמך, ומדורגת לפי מידת הוודאות שלה.""",
     """Two routes to the same point: from Wojsławice in the Lublin region and from
       Warsaw–Opatów, by way of Galicia, Volhynia and Dorohusk on the river Bug — to Israel.
       Every claim here rests on a document, and is graded by how certain it is.""",
     """Dwie drogi do tego samego punktu: z Wojsławic na Lubelszczyźnie oraz z Warszawy
       i Opatowa, przez Galicję, Wołyń i Dorohusk nad Bugiem — aż do Izraela.
       Każde twierdzenie opiera się tu na dokumencie i ma określony stopień pewności."""),
    ("<p class=\"tag\">צד אמא</p>", "<p class=\"tag\">Mother’s side</p>", "<p class=\"tag\">Strona matki</p>"),
    ("<p class=\"tag\">צד אבא</p>", "<p class=\"tag\">Father’s side</p>", "<p class=\"tag\">Strona ojca</p>"),
    ("""מוויסלביצה שבמחוז חלם, דרך שוייז'ה ודורוהוסק שעל נהר הבוג,
         וגם מראווה רוסקה שבגליציה האוסטרית. חנות משפחתית, בית בירה,
         וזיכרונות שנכתבו בעצם ידו של מנחם מנדל שאפיר.""",
     """From Wojsławice in the Chełm district, by way of Świerże and Dorohusk on the Bug,
         and also from Rawa Ruska in Austrian Galicia. A family shop, a beer house,
         and a memoir written in Menachem Mendel Schafir’s own hand.""",
     """Z Wojsławic w powiecie chełmskim, przez Świerże i Dorohusk nad Bugiem,
         a także z Rawy Ruskiej w Galicji. Rodzinny sklep, piwiarnia
         i wspomnienia spisane własnoręcznie przez Menachema Mendla Szafira."""),
    ("""מרובע היהודים של ורשה ועד אופטוב החסידית, דרך פיונטק ואיווניסקה.
         סיפור שנבנה מאקט נישואין אחד שנקרא במלואו, ומהחיפוש המתמשך
         אחר אשתו הראשונה של חיים אלברט ובתם, שנרצחו בשואה.""",
     """From the Jewish quarter of Warsaw to Hasidic Opatów, by way of Piątek and Iwaniska.
         A story built out of one marriage act read in full, and the continuing search
         for Chaim Albert’s first wife and their daughter, murdered in the Shoah.""",
     """Z żydowskiej dzielnicy Warszawy do chasydzkiego Opatowa, przez Piątek i Iwaniska.
         Historia zbudowana na jednym akcie małżeństwa odczytanym w całości i na wciąż
         trwających poszukiwaniach pierwszej żony Chaima Alberta i ich córki, zamordowanych w Zagładzie."""),
    ("<h2>כלי המחקר</h2>", "<h2>Research tools</h2>", "<h2>Narzędzia badawcze</h2>"),
    ("<h3>אילן יוחסין</h3>", "<h3>Family tree</h3>", "<h3>Drzewo genealogiczne</h3>"),
    ("<p>אינטראקטיבי — הקו הישיר שלכם מודגש, בלחיצה על כל אדם</p>",
     "<p>Interactive — click any person and their direct line is highlighted</p>",
     "<p>Interaktywne — kliknij osobę, a jej linia prosta zostanie wyróżniona</p>"),
    ("<h3>מפה</h3>", "<h3>Map</h3>", "<h3>Mapa</h3>"),
    ("<p>כל המקומות, מסומנים ומקושרים לפרקים</p>",
     "<p>Every place, marked and linked to its chapter</p>",
     "<p>Wszystkie miejsca, oznaczone i powiązane z rozdziałami</p>"),
    ("<h3>מסמכים</h3>", "<h3>Documents</h3>", "<h3>Dokumenty</h3>"),
    ("<p>סריקות ארכיון עם זום, ותרגום לצד המקור</p>",
     "<p>Archive scans with zoom, and a translation beside the original</p>",
     "<p>Skany archiwalne z powiększeniem i tłumaczeniem obok oryginału</p>"),
    ("<h3>נספח מקורות</h3>", "<h3>Sources</h3>", "<h3>Źródła</h3>"),
    ("<p>כל אקט, מאגר וספר שצוטט — עם ציטוט מלא</p>",
     "<p>Every act, database and book cited — with a full citation</p>",
     "<p>Każdy akt, baza i książka — z pełnym przypisem</p>"),
    ("<h3>חיפוש</h3>", "<h3>Search</h3>", "<h3>Szukaj</h3>"),
    ("<p>לפי שם עברי, לטיני, כתיב ארכיוני או מקום</p>",
     "<p>By Hebrew name, Latin name, archival spelling or place</p>",
     "<p>Według imienia hebrajskiego, łacińskiego, zapisu archiwalnego lub miejsca</p>"),
    ("<h3>מתודולוגיה</h3>", "<h3>Method</h3>", "<h3>Metodologia</h3>"),
    ("<p>איך חקרנו — הארכיונים, המלכודות, השיטה</p>",
     "<p>How the research was done — the archives, the pitfalls, the method</p>",
     "<p>Jak prowadzono badania — archiwa, pułapki, metoda</p>"),
    ("<h2>מה חדש</h2>", "<h2>What’s new</h2>", "<h2>Nowości</h2>"),
    ("""ענף מוסקל–אלספקטור–רייס (עד לייבה מוסקל, יליד ~1817) נוסף לעץ ולג'ני, מ"מסמכי 2019\"""",
     """The Moskal–Alspektor–Rajs branch (back to Lejba Moskal, b. ~1817) was added to the tree, from the “2019 documents”""",
     """Gałąź Moskal–Alspektor–Rajs (do Lejby Moskala, ur. ok. 1817) dodana do drzewa, na podstawie „dokumentów z 2019 r.”"""),
    ("""אקט פטירה 6/1833: אהרן ופרלה בוקשפן מדורוהוסק — האבות הקדומים ביותר במחקר""",
     """Death act 6/1833: Aron and Perla Bukszpan of Dorohusk — the earliest ancestors in the research""",
     """Akt zgonu 6/1833: Aron i Perla Bukszpanowie z Dorohuska — najdawniejsi przodkowie w badaniach"""),
    ("""אקט פטירה 4/1869: הקשר בין שוייז'ה לוויסלביצה, ומשפחת שיפמן–קץ""",
     """Death act 4/1869: the link between Świerże and Wojsławice, and the Szyfman–Kac family""",
     """Akt zgonu 4/1869: związek między Świerżami a Wojsławicami oraz rodzina Szyfman–Kac"""),
    ("<span>אנשים בעץ</span>", "<span>people in the tree</span>", "<span>osób w drzewie</span>"),
    ("<span>מתועדים במסמך ●</span>", "<span>documented ●</span>", "<span>udokumentowanych ●</span>"),
    ("<span>שנות היסטוריה</span>", "<span>years of history</span>", "<span>lat historii</span>"),

    # ── search ───────────────────────────────────────────────────────
    ("<p class=\"kicker\">חיפוש</p>", "<p class=\"kicker\">Search</p>", "<p class=\"kicker\">Szukaj</p>"),
    ("<h1>מי, איפה, מתי</h1>", "<h1>Who, where, when</h1>", "<h1>Kto, gdzie, kiedy</h1>"),
    ("""חיפוש מיידי בכל שמות המשפחה — עברית, לטינית, וכל כתיב ארכיוני
     שנמצא (שיפמן/SZYFMAN, שאפיר/SZAUFER, בוקשפן/BUKSZPAN ועוד).""",
     """Instant search across every family name — Hebrew, Latin, and every archival
     spelling found (Szyfman, Szaufer, Bukszpan and others).""",
     """Natychmiastowe wyszukiwanie wszystkich nazwisk — po hebrajsku, po łacinie
     i we wszystkich zapisach archiwalnych (Szyfman, Szaufer, Bukszpan i inne)."""),
    ('placeholder="חפשו שם, מקום, או כתיב…"',
     'placeholder="Search a name, a place, or a spelling…"',
     'placeholder="Szukaj nazwiska, miejsca lub zapisu…"'),
    ("'מקום'", "'place'", "'miejsce'"),
    ("both:'שני הענפים'", "both:'both branches'", "both:'obie gałęzie'"),
    ("'<p class=\"empty\">אין תוצאות</p>'",
     "'<p class=\"empty\">No results</p>'",
     "'<p class=\"empty\">Brak wyników</p>'"),

    # ── sources ──────────────────────────────────────────────────────
    ("<p class=\"kicker\">נספח</p>", "<p class=\"kicker\">Appendix</p>", "<p class=\"kicker\">Aneks</p>"),
    ("<h1>המקורות</h1>", "<h1>Sources</h1>", "<h1>Źródła</h1>"),
    ("""כל אקט, ספר, מאגר ומסמך משפחתי שצוטט באתר — עם ציטוט מלא ומיקום
     ארכיוני, כדי שכל טענה תהיה ניתנת לבדיקה עצמאית.""",
     """Every act, book, database and family document cited on this site — with a full
     citation and archival location, so that any claim can be checked independently.""",
     """Każdy akt, książka, baza danych i dokument rodzinny cytowany na tej stronie —
     z pełnym przypisem i lokalizacją archiwalną, aby każde twierdzenie można było sprawdzić."""),

    # ── documents ────────────────────────────────────────────────────
    ("<p class=\"kicker\">גלריה</p>", "<p class=\"kicker\">Gallery</p>", "<p class=\"kicker\">Galeria</p>"),
    ("<h1>המסמכים</h1>", "<h1>The documents</h1>", "<h1>Dokumenty</h1>"),

    # ── map ──────────────────────────────────────────────────────────
    ("<p class=\"kicker\">מפה</p>", "<p class=\"kicker\">Map</p>", "<p class=\"kicker\">Mapa</p>"),
    ("<h1>המקומות שהמשפחה עברה בהם</h1>",
     "<h1>The places the family passed through</h1>",
     "<h1>Miejsca, przez które przeszła rodzina</h1>"),
    ("""מדורוהוסק שעל נהר הבוג ועד חולון; מראווה רוסקה שבגליציה ועד ורשה.
     כל סמן הוא מקום שתועד במחקר, עם הפרק וקובצי המקורות שלו.""",
     """From Dorohusk on the Bug to Holon; from Rawa Ruska in Galicia to Warsaw.
     Every marker is a place documented in the research, with its chapter and sources.""",
     """Od Dorohuska nad Bugiem po Cholon; od Rawy Ruskiej w Galicji po Warszawę.
     Każdy znacznik to miejsce udokumentowane w badaniach, wraz z rozdziałem i źródłami."""),
    ("תורמי OpenStreetMap", "OpenStreetMap contributors", "współtwórcy OpenStreetMap"),
    ("אריחי מפה: ©", "Map tiles: ©", "Kafelki mapy: ©"),

    # ── tree ─────────────────────────────────────────────────────────
    ("<h1>אילן היוחסין</h1>", "<h1>The family tree</h1>", "<h1>Drzewo genealogiczne</h1>"),
    ("<p class=\"kicker\">העץ, ובתוכו הקו שלך</p>",
     "<p class=\"kicker\">The tree, and your own line inside it</p>",
     "<p class=\"kicker\">Drzewo i twoja własna linia</p>"),
    ("""בחרו אדם — בלחיצה על כרטיס או בחיפוש — והקו הישיר שלו, אבותיו
     וצאצאיו, יתבלט בעוד שאר הענפים נסוגים לרקע.""",
     """Choose a person — by clicking a card or by searching — and their direct line,
     ancestors and descendants, comes forward while the other branches recede.""",
     """Wybierz osobę — klikając kartę lub wyszukując — a jej linia prosta,
     przodkowie i potomkowie, zostanie wyróżniona, pozostałe gałęzie się wycofają."""),
    (">אילן מלא<", ">Whole tree<", ">Całe drzewo<"),
    (">פדיגרי<", ">Ancestors<", ">Przodkowie<"),
    (">צאצאים<", ">Descendants<", ">Potomkowie<"),
    (">שני הענפים<", ">Both branches<", ">Obie gałęzie<"),
    (">מתועד<", ">documented<", ">udokumentowane<"),
    (">סביר<", ">probable<", ">prawdopodobne<"),
    (">השערה<", ">inference<", ">wnioskowanie<"),
    ("· גרירה להזזה, גלגלת לזום",
     "· drag to pan, scroll to zoom",
     "· przeciągnij, aby przesunąć; przewiń, aby przybliżyć"),
    (">הכול<", ">All<", ">Wszystko<"),
]

IDX = {"en": 1, "pl": 2}


def main():
    changed = 0
    for lang, col in IDX.items():
        base = ROOT / lang
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.html")):
            html = p.read_text(encoding="utf-8")
            before = html
            for row in sorted(PAIRS, key=lambda r: -len(r[0])):
                if row[0] in html:
                    html = html.replace(row[0], row[col])
            if html != before:
                p.write_text(html, encoding="utf-8")
                changed += 1
    print(f"core strings translated in {changed} page(s)")


if __name__ == "__main__":
    main()
