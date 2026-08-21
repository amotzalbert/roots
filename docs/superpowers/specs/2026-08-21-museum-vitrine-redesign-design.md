# «שורשים» — The Vitrine redesign

**Date:** 2026-08-21
**Status:** approved in brainstorming, awaiting spec review
**Scope:** complete visual redesign of all 70 HTML pages across `he` / `en` / `pl`

---

## 1. What this is

The site is replaced with a single new design system called **The Vitrine** — a
daylit modern museum hall. Cool mineral plaster walls, objects raised on plinths
with real cast shadows, very heavy Hebrew sans set large, and citations visible
in the open rather than hidden behind interaction.

The previous archival paper-and-ink direction is retired, not refined. Its
beige-paper ground, Frank Ruhl serif body text, and thin red rule are removed.

### Why this direction

Three audiences, all of whom need the same thing:

| Audience | Need | What the design does |
|---|---|---|
| Family, including older relatives | Legibility above all | Light ground, high contrast, large type, conventional nav |
| Genealogy researchers, distant kin | Evaluate evidence fast | Citations always visible; act numbers never hidden |
| Amotz | A working instrument | Density where it counts; interactive tools untouched |

No audience wants novelty in the navigation, so the navigation stays
conventional. The design's boldness is spent entirely on typography and the
plinth treatment.

### Explicit non-goals

- Not a portfolio piece. Legibility beats memorability at every conflict.
- No new content, no new pages, no restructured information architecture.
- No changes to `tree.js`, `tree-views.js`, or the Leaflet map behaviour.
- No build step, no framework, no dependencies. It stays static HTML + CSS.

---

## 2. Architecture: shared page stylesheets

### The problem

Every page carries its own inline `<style>` block, and those blocks are
**byte-identical across the three language trees** (verified by hash for
`index`, `tree`, `documents`). There are 1,393 lines of inline CSS across 70
files, roughly two-thirds of it pure triplication.

Redesigning in place would mean authoring every page's CSS three times, and
each of those edits would land inside a file marked `ROOTS-TRANSLATED: done` —
the exact files the mirror script protects.

### The change

Lift every inline `<style>` block into `css/pages/<page>.css`. All three
language copies link the same file.

```
css/
  main.css            tokens, resets, shared chrome
  pages/
    home.css          index.html
    tree.css          tree.html
    documents.css     documents.html
    map.css           map.html
    sources.css       sources.html
    methodology.css   methodology.html
    search.css        search.html
    research.css      research.html
    research-index.css research-index.html
    branch.css        both branch index pages
    chapter.css       all 14 ch-*.html pages
```

`branch.css` and `chapter.css` are shared across pages of the same type — the
chapter pages' inline blocks are 10–22 lines each and largely overlap.

### Why this eliminates the translation risk rather than managing it

`tools/mirror-langs.py` already treats `css/` as a shared path and rewrites
`css/pages/home.css` to `../css/pages/home.css` when mirroring. But it refuses
to overwrite any target containing `ROOTS-TRANSLATED: done`, so the already-
translated `en` and `pl` pages will never be re-mirrored.

Therefore the `<link>` insertion into translated pages is done by a separate,
idempotent script — **not** by the mirror script:

**`tools/extract-page-css.py`**

1. **Verify the triplication assumption per page.** Byte-identity across
   `he`/`en`/`pl` was confirmed by hash for `index`, `tree` and `documents`
   only — it is assumed, not proven, for the other 21 page types. The script
   hashes all three copies of every page's `<style>` block first and aborts the
   entire run if any page's three copies differ. A page whose language copies
   have diverged needs a human decision, not an automatic merge.
2. For each Hebrew source page, extract the `<style>` block to the mapped
   `css/pages/*.css` file. Where several pages map to one stylesheet
   (`chapter.css`), merge and de-duplicate rules, and fail loudly on any
   conflicting declaration for the same selector rather than silently picking
   one.
3. In every one of the 70 HTML files — Hebrew, English and Polish alike —
   delete the `<style>` block and insert
   `<link rel="stylesheet" href="{prefix}css/pages/<page>.css?v=<stamp>">`
   immediately after the existing `main.css` link, where `{prefix}` is `""` for
   the Hebrew tree and `"../"` for `en`/`pl`.
4. Touch nothing outside `<head>`. The script asserts that the `<body>` of every
   file is byte-identical before and after, and aborts the whole run if any
   file's body changes.
5. Re-running the script on an already-converted tree is a no-op.

This takes the styling out of the translated files permanently. Every subsequent
design change edits `css/`, which no translated page owns, so translated content
cannot be clobbered by a design edit. The risk goes to zero rather than being
carefully managed on each change.

### Verification for this step

Before/after full-page screenshots of all 70 pages must be pixel-identical. This
step is a pure refactor: it changes where CSS lives, never what it says. Any
visual difference at this stage is a bug in the extraction, and the redesign
does not begin until this step is provably invisible.

---

## 3. The design system

`main.css` becomes tokens, reset, and shared chrome only. All page-specific
rules live in `css/pages/`.

### 3.1 Colour

Light-first. The dark theme is designed as its own set, not derived by
inversion.

**Light (default)**

| Token | Value | Role |
|---|---|---|
| `--wall` | `#E3E5DF` | Page ground. Cool mineral plaster |
| `--plinth` | `#F4F5F1` | Raised object surface |
| `--plinth-2` | `#ECEEE8` | Recessed / secondary surface |
| `--ink` | `#1E2320` | Primary text |
| `--ink-2` | `#4A504A` | Secondary text |
| `--ink-3` | `#6B716A` | Labels, captions, metadata |
| `--rule` | `#C9CCC3` | Hairlines and dividers |
| `--rule-heavy` | `#1E2320` | The 2px rule under the tally |
| `--accent` | `#8C3B2E` | Iron red. Current state and emphasis only |

The neutrals carry a slight green bias so they read as chosen rather than
inherited mid-grey. `--accent` is never used decoratively and never used for a
branch.

**Dark**

| Token | Value |
|---|---|
| `--wall` | `#1A1D1B` |
| `--plinth` | `#232724` |
| `--plinth-2` | `#1E211F` |
| `--ink` | `#E8EAE4` |
| `--ink-2` | `#AEB4AC` |
| `--ink-3` | `#848A82` |
| `--rule` | `#343833` |
| `--rule-heavy` | `#E8EAE4` |
| `--accent` | `#D4705E` |

The dark accent is lightened and desaturated from the light one so it holds
contrast on a dark ground; it is not the same hex.

**Branch colours — unchanged**

`--moskal: #B5601A` and `--albert: #5A5478` (dark theme: `#E08A45` / `#9C95C4`)
carry across `tree.js`, the map, and the documents table. They encode real
information and are deliberately not repainted. `--ok: #4A6A5A` likewise stays
as the "documented ●" marker.

### 3.2 Type

**Hebrew: Heebo**, self-hosted, OFL licensed. Weights 400 / 500 / 700 / 900,
subset to Hebrew + Latin + punctuation, `woff2`, `font-display: swap`.

**Latin (`en` / `pl`): Archivo**, self-hosted, OFL licensed. Chosen for complete
Polish diacritic coverage (ą ć ę ł ń ó ś ź ż) and for sitting properly beside
Heebo's grotesque proportions.

**Citations and figures: Roboto Mono**, self-hosted, OFL licensed.

Self-hosting is required: the current `@font-face` rules use `local()` only, so
any visitor without Frank Ruhl Libre installed silently falls back to Times. The
new faces ship with the site.

**Scale** — one modular scale at 1.25, from `0.72rem` to `5.6rem`. Display
sizes use Heebo 900 with `letter-spacing: -0.03em`; the negative tracking is
applied only at `2rem` and above, never to body text.

`font-variant-numeric: tabular-nums` on every element where digits column up:
the tally, act numbers, person counts, year ranges, the documents table.

**Minimum sizes (hard floor, for the older-relatives constraint)** — body text
never below `1.05rem`; labels and captions never below `0.78rem`; no weight
below 400 at any size.

⚠ **This floor overrides the approved mockup.** The mockup sets branch tags at
`0.66rem` and citations at `0.7rem`; both are raised to `0.78rem` in production,
with letter-spacing reduced from `0.18em` to `0.12em` to compensate for the
extra width. The mockup is the reference for composition and colour, not for
label sizing. If raising them damages the composition, the fix is to change the
composition — the floor does not move.

### 3.3 Theming mechanics

The existing `ROOTS-THEME-BOOT` inline script and `data-theme` attribute are
kept as-is — they work, and they run before first paint. Token blocks are
defined for bare `:root` (light), `@media (prefers-color-scheme: dark)` guarded
as `:root:not([data-theme="light"])`, and `:root[data-theme="dark"]`. No colour
is ever declared outside a token block.

---

## 4. Component vocabulary

Six components, defined once in `main.css`, used everywhere. No page invents its
own furniture — this is what keeps 70 files coherent.

| Component | What it is | Where it appears |
|---|---|---|
| **plinth** | Raised surface, 4px branch-coloured top edge, cast shadow, citation foot | Home, branch indexes, documents |
| **tally** | Row of large figures over a 2px rule | Home, branch indexes |
| **index row** | Numbered row: number, title + subtitle, right-aligned count | Documents, sources, research-index, search results |
| **citation** | Roboto Mono, inline, always visible, never hover-revealed | Everywhere a claim is made |
| **artifact frame** | Bordered container for a scan, headstone photo, or document image, with a caption block | Chapters, documents, sources |
| **nav** | Sticky top bar: brand, page links, language switcher, theme and font-size controls | Every page |

The nav keeps its current link set and order. The language switcher, theme
toggle and font-size control keep their current behaviour and their `ui.js`
wiring; only their styling changes.

---

## 5. Page application

| Page | Treatment |
|---|---|
| `index.html` | The approved mockup: hero with oversized `שורשים`, tally, two branch plinths |
| `documents.html` | Index rows, one per document, citation in the right column |
| `sources.html` | Index rows grouped by archive |
| `research-index.html` | Index rows, one per report |
| `research.html` | Long-form: artifact frames, pull quotes, citations |
| `methodology.html` | Long-form, no plinths — this page is argument, not objects |
| `search.html` | Index rows as results; search field styled as a plinth |
| `tree.html` | **Retokenised only.** Chrome restyled; `tree.js` and `tree-views.js` untouched |
| `map.html` | **Retokenised only.** Leaflet popups restyled via tokens; map behaviour untouched |
| `moskal-szafir/index.html`, `albert-rywenbajrych/index.html` | Branch tally + chapter plinths |
| 14 × `ch-*.html` | Long-form chapters: artifact frames, citations, running heads |

`tree.html` and `map.html` are working instruments. Their JavaScript is not
touched for aesthetic reasons — the tree carries a 258-person GEDCOM rendering
with three view modes, and breaking it to restyle it would be a bad trade.

---

## 6. Motion

**One orchestrated page-load, and nothing else.**

On load: the tally figures and then the plinths reveal in a stagger, ~400ms
total, opacity plus a 8px rise. Nothing else on the page animates on load.

Ongoing interaction is limited to a plinth lift on hover (`translateY(-2px)`,
120ms) and visible focus rings on every interactive element.

No scroll-triggered reveals, no parallax, no ambient motion, no counters that
count up. Scattered micro-interactions are the main thing that makes a page read
as machine-generated, and one composed moment lands harder than ten small ones.

Everything above is wrapped in `@media (prefers-reduced-motion: no-preference)`.
With reduced motion requested, the page renders in its final state immediately.

---

## 7. Verification

The redesign is not complete until all of the following pass.

1. **Extraction is invisible.** All 70 pages pixel-identical before/after the
   CSS extraction step (section 2).
2. **No translated content changed.** `git diff` across `en/` and `pl/` shows
   changes confined to `<head>`. Any diff line inside `<body>` fails the build.
3. **Contrast.** Every text/ground pair meets WCAG AA *at its actual rendered
   size and weight*, in both themes, measured rather than assumed.
4. **Three widths × three languages.** Screenshots at 375 / 768 / 1440 for
   `he`, `en`, `pl`. RTL and LTR both correct; no horizontal body scroll at any
   width.
5. **Polish diacritics render.** ą ć ę ł ń ó ś ź ż present and correctly formed
   in Archivo at display and body sizes.
6. **Fonts actually load.** No silent fallback: verified by computed-style check,
   not by eye.
7. **Tools still work.** Tree renders all three view modes; map markers and
   popups work; search returns results; language switcher preserves `?f=` /
   `?p=` and anchors.
8. **Theme toggle.** Light, dark, and system-default all render correctly, with
   no flash of wrong theme on load.

---

## 8. Order of work

1. `tools/extract-page-css.py` — extraction, with the pixel-identical gate
2. `main.css` — tokens, fonts, reset, nav, the six components
3. `home.css` — the reference implementation, all three languages
4. Remaining page stylesheets
5. `tree.css` / `map.css` — retokenisation only
6. Full verification sweep

Step 1 must be provably invisible before step 2 begins. Step 3 is the point at
which the direction is either right or wrong; if it's wrong, that's the moment
to say so, before the remaining eight stylesheets are written against it.

---

## 9. Open decisions deferred to implementation

None. Every decision needed to begin is recorded above.
