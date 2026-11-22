# Design v2 — "The World on 21 November 2026"

Square 1024 × 1024 poster, pure white background, only two inks: black and
Economist red #E3120B. Flat silhouette editorial illustration in the grammar of
The Economist's "The World Ahead" covers. The whole poster, lettering included,
is drawn by the image model from `image-prompt-v2.txt`; `main.py` only carries
the result to `/output/entry.png`.

The governing rule: **the circle holds pictures only.** Every word sits on the
white paper outside the circle, next to the motif it belongs to.

## Canvas, top to bottom (pixel guide for a 1024 canvas)

| Band | y (px) | Content |
|---|---|---|
| Margin | 0–36 | white |
| Kicker | 36–72 | small solid red rectangle, centred, with white text `ONE DAY · ONE PICTURE` |
| Title line 1 | 84–140 | `THE WORLD ON`, black, bold condensed, centred, cap height ≈ 52 px |
| Title line 2 (date) | 150–252 | `21 NOVEMBER 2026`, black, heaviest condensed, centred, cap height ≈ 100 px, spans ≈ 85–90 % of the width |
| Rule | 268 | thin black horizontal rule, full margin width |
| Picture band | 290–930 | the circle in the middle, four label blocks on its flanks, one label block below it |
| Rule | 948 | thin black rule |
| Footer | 962–992 | `SATURDAY · FIVE STORIES · ONE DAY`, small black, centred, letter-spaced |

## The circle

- Centre (512, 575), diameter ≈ 470 px (x 277–747, y 340–810): about 46 % of
  the width — the biggest element on the page after the date.
- Thin black outline (≈ 3 px), white inside.
- Five motifs arranged like the points of a pentagon with one point down,
  each filling its sector, generously sized (≈ 170–200 px each), allowed to
  touch and interlock slightly so the circle reads as one globe-like whole,
  never as five stickers:

| Story | Position inside the circle | Motif |
|---|---|---|
| 1 Mexico | upper left (≈ 10–11 o'clock) | black handcuffs, red police badge (blank star badge, no lettering) |
| 2 Kryvyi Rih | upper right (≈ 1–2 o'clock) | black missile diving down, red starburst, black city skyline below it |
| 5 Dengue | right, lower (≈ 4 o'clock) | big black mosquito in profile, red shield in front of it, red virus particle crossed out with a bar |
| 3 COP31 | bottom centre (≈ 6 o'clock), rising toward the centre | black globe, red thermometer, white ice cap dripping/melting |
| 4 BepiColombo | left, lower (≈ 8 o'clock) | black cratered planet Mercury, spacecraft with long red/black solar panels beside it |

No text of any kind inside the circle: no letters, digits, percent signs,
logos, flags with writing, map labels or tick numbers on the thermometer.

## Label blocks (all outside the circle)

Each block = headline (black, bold condensed, uppercase, two lines) + sublabel
(red, smaller, uppercase, one or two lines). Side blocks are 210–230 px wide in
the side margins (x 40–262 on the left, x 762–984 on the right).

| Block | Position | Headline (lines) | Sublabel (lines) | Tie to motif |
|---|---|---|---|---|
| 1 | left margin, upper (y ≈ 330–460), right-aligned toward the circle | `MEXICO CAPTURES` / `CARTEL BOSS` | `EL CHAPO ISIDRO ·` / `FBI MOST WANTED` | short thin black leader line from the block's inner edge to a small solid red dot on the circle outline at 10 o'clock, beside the handcuffs |
| 2 | right margin, upper (y ≈ 330–460), left-aligned toward the circle | `RUSSIAN STRIKE` / `HITS KRYVYI RIH` | `2 KILLED · 60 WOUNDED` | leader + red dot at 2 o'clock, beside the missile |
| 4 | left margin, lower (y ≈ 620–750), right-aligned | `BEPICOLOMBO` / `REACHES MERCURY` | `8-YEAR VOYAGE ·` / `ESA & JAXA` | leader + red dot at 8 o'clock, beside the spacecraft |
| 5 | right margin, lower (y ≈ 620–750), left-aligned | `MOSQUITOES CUT` / `DENGUE 69%` | `BRAZIL TRIAL ·` / `5,700 CHILDREN` | leader + red dot at 4 o'clock, beside the mosquito |
| 3 | centred under the circle (y ≈ 835–925) | `COP31 TALKS RUN INTO OVERTIME` (one line) | `ANTALYA · NO FOSSIL-FUEL DEAL` | short vertical leader + red dot at 6 o'clock, right above the globe |

COP31 has the longest headline (29 characters), so it gets the only full-width
slot; the four side headlines are each at most 15 characters per line.

## Type hierarchy

1. Date `21 NOVEMBER 2026` — heaviest black condensed, cap ≈ 100 px (≈ 29 px
   at 300 px wide). The single largest text.
2. `THE WORLD ON` — black bold condensed, cap ≈ 52 px.
3. Story headlines — black bold condensed, cap ≈ 26–28 px (≈ 8 px at 300 px
   wide); the COP31 line the same size.
4. Sublabels — red #E3120B, bold condensed, cap ≈ 16–17 px.
5. Kicker `ONE DAY · ONE PICTURE` — white on a red block, cap ≈ 18 px.
6. Footer — black, regular weight, letter-spaced, cap ≈ 16 px.

All lettering uppercase sans-serif; black is near-black (#111111) for text and
silhouettes, red is exactly #E3120B, background exactly white.

## Why this layout beats the alternatives

**Criterion 1 (names the day).** The date is the largest, highest-contrast
object on the page and sits at the top, where a reader — or a vision judge —
looks first; at 300 px wide it is still about 29 px tall. "THE WORLD ON"
directly above turns it into a sentence ("The world on 21 November 2026"), and
the footer repeats SATURDAY, so the day is stated twice in different ways.
Alternatives that put the date in a small corner tag or the footer make
criterion 1 depend on fine print.

**Criterion 2 (breadth).** The five blocks are spread across the page so the
mix — Latin America crime, Europe war, climate diplomacy in Turkey, space
science, public health in Brazil — is visible as five equal-weight items, not a
lead story plus sidebars. No story is larger than another except COP31's
wider, not taller, slot.

**Criterion 3 (reads without context).** Each headline is a full subject–verb
sentence with the key fact in the sublabel (2 killed · 60 wounded; 69 %;
8-year voyage), and it sits physically beside the picture it explains, joined
by a leader line and a red dot. Proximity plus a line is the strongest
picture–caption tie there is; a numbered legend under the circle would need
numbers inside the circle (forbidden) and forces the eye to commute.

**Criterion 4 (faithful).** Labels use the reported facts verbatim; no
superlatives, no forecasts ("NO FOSSIL-FUEL DEAL" describes the draft as
reported, not the final outcome).

**Criterion 5 (craft, 300 px).**
- Text on plain white outside the picture never fights the illustration, and
  an image model renders text far more reliably on empty paper than over
  detailed artwork — the old in-circle labels were the main source of clutter.
- Few, large, short text blocks: 14 strings, each line ≤ 29 characters, side
  lines ≤ 15 characters, which keeps per-glyph size up and garbling risk down.
- One composition: masthead → one circle → footer, symmetric about the
  vertical axis.
- Rejected: labels in a column beside a left-shifted circle (leader lines
  would cross the other motifs); labels in a grid under the circle (shrinks
  the circle and loses proximity); a full-bleed illustration with captions
  over it (illegible at 300 px and against the no-text-in-circle rule).

## Production notes

- Generate at 1024 × 1024 (square). If the model returns a larger square,
  `main.py` box-averages it down to fit 1024 × 1024 and guarantees ≤ 1 MiB.
- Before placing `poster.png`, check by eye: every string spelled exactly,
  nothing inside the circle that looks like a letter or number, no stray
  captions, red is red and not orange.
