---
name: caption-cards
type: object
cluster: artifacts
universe: live
status: verified
verified: 2026-08-26
---

# Caption cards

`02-caption-cards.json` — the words grouped into phrase cards, each already wrapped into display lines. `02-captions.srt` is the same data in a portable format.

## Why this shape

**The lines are pre-wrapped here and never re-wrapped downstream** (`remotion/src/types.ts:24`). The character budget was derived from Inter SemiBold's advance width, so wrapping anywhere that does not know the font would stop describing the pixels — and the longest lines, the ones nearest the margin, are exactly the ones that would overflow.

`wrap()` returns `None` for a card it cannot lay out (`chunk_captions.py:44-95`), and callers must read that as *close this card earlier*. An earlier version sliced at the character count and shipped `"so the thing abou"` / `"t pricing that"`.

**Cards run wall-to-wall.** Card N ends the frame card N+1 begins (`chunk_captions.py:363-365`), bounded by `max_duration_s` so a deliberate pause does not sit under the previous sentence.

## Shape

`chunk_captions.py:411-417` — `topic`, `duration`, `chars_per_line`, `pacing_overrides`, `cards[]`.
Each card: `index`, `text`, `lines[]`, `start`, `end`, `words`, `duration`, `chars_per_second` (`chunk_captions.py:344-379`).

`chars_per_line` is **recomputed at runtime** from geometry ÷ font size, not read from config; a disagreement with the stored value prints a warning and the derived number wins (`chunk_captions.py:307-312`).

The `.srt` is written every run as a byproduct, and nothing downstream reads it — Remotion burns from the cards. It exists because it is the one caption artifact that outlives this workspace (`write_srt.py:5-11`).

## Connected to

- **owned by** — [[run-folder]]
- **consumes** — [[transcript]], [[edit-defaults]] `caption:` + `geometry:` + `typography:`, [[preferences]] § Pacing
- **feeds** — [[remotion-props]]
- **looks like but is not** — the `.srt`, which loses word-level timing. Nothing is lost on screen, since the display is phrase-chunked anyway.

## If you change this

**Hits**
- **Any typography or geometry change** re-derives `chars_per_line` and re-splits every card. `caption_size_px` and `max_lines` move together — see [[edit-defaults]].
- **A pacing override** in `memory/preferences.md` § Pacing is applied here and recorded in the file as `pacing_overrides` (`chunk_captions.py:292-298`).
- **Changing the card schema** hits `write_srt.py`, `render_captions.py:189-192`, `remotion/src/types.ts:13-22`, and the ten-odd caption assertions in `tools/run_fixture_checks.py:182-251`.

**Does not hit**
- **The transcript.** Nothing here writes back. Re-chunking is free and repeatable.
- **The under-floor cards left after `join_underfloor`.** Those are reported, not bugs (`chunk_captions.py:433-449`) — the only lever that clears them is a second row, which is a `max_lines` decision, not a chunker fix.

## Surfaces

Written by `chunk_captions.py`, read by `write_srt.py` and `render_captions.py`. Hand-editable, though a re-run of stage 02 overwrites it.

## See

`stages/02_assemble/scripts/chunk_captions.py:277-469` · `stages/02_assemble/CONTEXT.md`
