# Style lock — «שורשים» roots site

## Active direction: «ארכיון שחור» (Archive Noir), 26 Aug 2026 — branch redesign/archive-noir
Chosen by Amotz from a 3-comp shootout (__comps/: a-noir ✓ · b-atlas · c-gallery).
Documentary-brutalist. DARK IS THE PRIMARY IDENTITY: deep black wall (#0d0c0b), the
archive scans themselves full-bleed as hero/section imagery, huge Heebo Black type,
one blood-red accent, hard visible rules, mono catalog labels.
LIGHT MODE = «printed catalog»: the exact same system on white paper — hard black
rules, same red, gray-scaled scans. Not a soft inversion. Theme toggle (system/
light/dark) preserved as before.

## Type
Heebo Black 900 display + body (Archivo for en/pl UI), Roboto Mono for act numbers,
dates, nav links, kickers (letter-spacing .35–.5em). NO serif (FRL stays shipped but
unused). Display clamp(3.6rem,11vw,8.5rem).

## Color contract (all pairs AA, 0 failures, 26 Aug 2026)
Dark: wall #0d0c0b · plinth #141311 · ink #f2efe9 · ink-2 #b8b3a8 · ink-3 #948f83
· accent(text) #ff5a4d · accent-fill #d92c1f (white-on-fill 4.85) · moskal #ff9d3f
· albert #8f9bff · ok #69d29a · gold #d9b25f.
Light: wall #f6f4f0 · plinth #fff · ink #141311 · accent(text) #c22415 · fill #d92c1f
· moskal #a24d0d · albert #4f57b8 · ok #2c7a4b · gold #77601a.
--accent (text-safe) vs --accent-fill (fills/bars, white text) are SEPARATE tokens.
Branch photo panels (.bcard on home) are constant-dark in both themes.

## Motifs
- Scan-wall hero (m-1839-M01.jpg full-bleed, theme-dependent treatment) — CSS-only
  via .hero::before/::after; full-bleed strips use margin-inline:calc(50% - 50vw)
  + body{overflow-x:clip}.
- Red census band (.stats/.tally) — full-bleed accent-fill strip, white 900 numerals.
- Catalog drawers: list rows that indent on hover via transform:translateX(calc(var(--fwd)*…))
  (--fwd:-1 RTL / 1 LTR) — never padding animation.
- Tree: sharp corners (CSS rx:0 overrides SVG attr), branch tint cards, thick
  spines, red focus stroke. Tint strength is THEME-DEPENDENT (--tree-mix: 30% light /
  18% dark; white canvas + darker strokes + gentler fade in light) — fixed 26 Aug after
  Amotz flagged the washed-out light tree. Formula in tree.css.
- Sharp corners everywhere (border-radius:0), 1px rules + 1px heavy rules, no soft chrome.
- Emoji icons hidden by CSS (.tcard .ic{display:none}), arrows via ::after with
  :lang() direction flip.

## Motion
One load moment (noir-rise .5s), IO scroll reveals (ui.js, reduced-motion safe),
readbar via transform:scaleX (transform-origin flips for RTL). Hover: background +
transform indents at .16s, image zoom .35s, all gated (hover:hover) and (pointer:fine).
scaleX(0) on .readbar is a progress bar at rest — a known audit false-positive.

## Hard constraints (project) — unchanged
- NEVER touch translated text in en/ + pl/. CSS/JS-only; class names = frozen API.
- tree.css/map.css restyle via tokens only; tree.js/map JS untouched.
- Certainty grading ● ◐ ○ carries research meaning.
- Legacy aliases --paper/--paper-2/--paper-3/--rule-2/--shadow stay mapped.

## History
- v1 (pre-Aug-21): serif via local() only. v2 «ויטרינה» (21 Aug, merged): flat museum.
- v3 «חדר הקריאה» (26 Aug, commit 7a03902 on this branch's history): paper/serif
  two-zone — built, then rejected by Amotz as too close to v2.
- v4 «ארכיון שחור» (26 Aug, this lock): chosen from comps. LESSON RECORDED: Amotz
  wants redesigns to be RADICAL — new palette, new layout, new component shapes —
  not a token reskin. Show 2-3 real comps and let him choose before rolling out.
