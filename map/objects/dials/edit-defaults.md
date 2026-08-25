---
name: edit-defaults
type: object
cluster: dials
universe: live
status: verified
verified: 2026-08-26
---

# Edit defaults

`_config/edit-defaults.yaml` — every operative value in the workspace. No threshold, size, or path may appear in a script.

## Why this shape

**The `rules:` / `diagnostics:` split is the file's most important structure**, and it is enforced at load: `pipeline_lib.py:59-66` exits if either key is missing. A flat list is what let four caption values sit together looking equally binding when they could not all be true at once. `rules:` violations are bugs; `diagnostics:` are measured, printed, and acted on by nothing.

Every value carries the spec line it came from and, where it departs from the spec, the reason and date. That inline record is the file's real content — this card does not restate it.

## Shape

Four rule blocks and three diagnostics.

`rules: caption:` timing and splitting · `geometry:` canvas, safe zone, anchor, width · `typography:` font, size, colour · `audio:` → [[audio-block]] · `render:`
`diagnostics: words_per_card`, `chars_per_second_flag_over`, `heard_window_s`

**Three values move together and cannot be changed alone** (`edit-defaults.yaml:63-71,160,168-181`):

```
max_lines  ←→  caption_size_px  ←→  chars_per_line_derived
   1              44 px               25
```

`chars_per_line` is **recomputed at runtime** from `max_line_width_px ÷ (caption_size_px × avg_char_advance_em)` (`chunk_captions.py:307-312`). The stored `chars_per_line_derived` is a record of the arithmetic; a mismatch prints a warning and the derived value wins. `max_line_width_px: 580` is itself derived as `2 × (540 − 250)` — the right margin binds.

`44` rather than `46` is one character wide on purpose: "the worse the output gets" is 25 characters and the person named it as a phrase they wanted whole.

## Ghosts — 14 keys no code reads

Verified 2026-08-26 by grep across `stages/`, `tools/`, `remotion/src/`, and the root scripts. **Changing one of these changes nothing.**

| Key | Note |
|---|---|
| `resolution` | `render_captions.py:203` uses `geometry.canvas`. Two canvas sizes in one file, one of them inert. |
| `safe_zone` | only `bottom_limit_px` is asserted; the four margins are documentation |
| `single_export_serves` | provenance |
| `caption_motion` | **read by nothing and still load-bearing** — a written refusal of popping captions, deliberately not named "animation" |
| `lead_in_s`, `gap_between_cards_s` | both `0.0`; held by construction in the wall-to-wall extend loop |
| `prefer_fewest_cards`, `preserve_quotes` | describe `build_cards` behaviour rather than switch it |
| `allow_orphan_cards` | appears only in a docstring, `chunk_captions.py:221` |
| `anchor_semantics`, `allow_serif`, `hierarchy_via`, `background_box`, `subtitles_topmost` | documentation |
| `max_words_per_card` | documented as unreachable — the 2.5 s ceiling caps a card near 8 words |

Most are honest statements of a property held elsewhere. The one that reads as a real hazard is `resolution`, which looks like the frame size and is not.

## Connected to

- **overridden by** — [[preferences]], per deployment, one key at a time
- **read by** — `chunk_captions.py`, `render_captions.py`, `measure.py:56`, via [[pipeline-lib]]
- **looks like but is not** — [[paths]], the only file that may hold a filesystem path
- **provenance** — `reference/source-specs/` and `EXCLUSIONS.md`. **No script opens these**, and `run_fixture_checks.py:324` asserts it.

## If you change this

**Hits**
- **A `typography:` or `geometry:` change** re-derives the character budget, so **re-run `chunk_captions.py`, not just the render** — the line breaks in an existing `02-caption-cards.json` were fixed against the old budget.
- **Merging `rules:` and `diagnostics:`** stops every stage at load.
- **Any edit here triggers the fixture checks** — `_config` is in `sync.py`'s `CHECK_DIRS` (`tools/sync.py:34`).
- **Promoting a diagnostic to a rule** is a real decision: captions track speech at zero gap, so word count and reading speed cannot be enforced without breaking duration.

**Does not hit**
- **The source specs.** They are provenance; the extraction happened once, by hand.
- **The Remotion side.** It holds no constants — every value arrives as props (`remotion/src/types.ts:1-10`).
- **Anything at all**, for the 14 ghost keys above.

## Surfaces

Hand-edited by the person. Read by three stages. Never written by code — `governance.md` rule 2.

## See

`_config/edit-defaults.yaml` · `pipeline_lib.py:54-75` · `CONTEXT.md`, "Shared resources"
