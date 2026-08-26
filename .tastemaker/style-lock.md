# Style lock — «שורשים» roots site

## Active direction: «חדר הקריאה» (Reading Room), Aug 2026 — branch redesign/reading-room
Two-zone archival system per book-serif-index: dark catalog shell (topbar+footer, dark in
BOTH themes) framing a warm paper page. Light = reading room by day; dark = archive by
lamplight (independent system, not an inversion).

## Type
- Reading (body, headings, display): 'Frank Ruhl Libre' variable 400–900, self-hosted
  woff2 subsets (hebrew / latin / latin-ext) in assets/fonts. Serif is the identity.
- Utility (nav, labels, buttons, kickers): Heebo (he) / Archivo (en+pl).
- Catalog (act citations, numbers, dates): Roboto Mono. tabular-nums everywhere numeric.
- Scale: labels .78rem floor, body 1.08rem/1.85, display clamp(3.2rem,8.5vw,6rem).

## Color contract (all pairs checked, 0 failures, both themes — 26 Aug 2026)
Light: wall #efe9dc · plinth #f8f4ea · ink #26211a (13.2:1) · ink-2 #4f4939 · ink-3 #675f4d
· accent #7c2d21 (registry-margin oxblood, 7.7:1) · moskal #a3541a / ink #7d420e
· albert #57517a / ink #454064 · ok #44614b · gold #7c6526.
Shell (theme-invariant dark): #211c14 · ink #ece4d0 · ink-2 #b0a58a (6.9:1) · accent #d68a64
· moskal-sh #dc9448 · albert-sh #a8a0d4.
Dark: wall #191611 · plinth #221e17 · ink #eae2cd · accent #d98f68 — all body pairs ≥5:1.
Branch colors CARRY DATA (tree.js/map/documents) — never repaint decoratively.

## Motifs
- Registry margin line: 3-4px branch-color border-inline-start on folio cards (.plinth,
  .bcard, .introcard) — the red margin rule of Polish registry books.
- Double rules (3px double) above ledgers/indexes/footnotes; h2 gets thin double via ::after.
- Paper grain: feTurbulence data-URI at slope .045 on body.
- Artifact = plate: paper mat padding + thin frames. Lightbox stays a darkened room.
- §-numbered h2 in chapters (CSS counters — language-neutral). ❦ in footer colophon.

## Motion
One orchestrated load moment (.reveal / folio-rise 550ms, cubic-bezier(.22,.61,.36,1)),
IntersectionObserver scroll reveals (10px rise, 600ms) auto-tagged by ui.js — hidden only
under html.js + no-preference. Hover lifts: transform + opacity-animated ::before shadow
layer, gated @media (hover:hover) and (pointer:fine). Reading progress bar (.readbar) on
.chapter-meta/.md pages. Editorial budget: entrances 500–760ms, controls 140–180ms.

## Hard constraints (project)
- NEVER touch translated text in en/ + pl/ (ROOTS-TRANSLATED:done). CSS/JS-only redesigns;
  markup contracts (class names) are frozen API.
- All 68 pages × 3 languages share main.css + css/pages/*; tree.css/map.css are token-driven
  (SVG reads CSS vars) — redesign via tokens, don't restructure.
- Certainty grading ● ◐ ○ (.g-*) carries research meaning — keep visible, never decorative.
- Legacy aliases --paper/--paper-2/--paper-3/--rule-2/--shadow must stay mapped.
- Emoji tool icons (🌳🗺️📜…) are content in protected trilingual markup — replace only in a
  pass that edits all 3 languages deliberately.

## History
- v1 (pre-Aug-21): Frank Ruhl via local() only (broken fallback to Times).
- v2 «ויטרינה» (merged 21 Aug, branch redesign/museum-vitrine): flat daylight museum,
  Heebo-Black-only, plinth cards with colored top bars.
- v3 «חדר הקריאה» (26 Aug, branch redesign/reading-room): this lock.
