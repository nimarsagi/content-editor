---
name: tallies
type: object
cluster: dials
universe: live
status: verified
verified: 2026-08-26
---

# Tallies

Two files in `memory/` that code writes without asking. Both are exempt from the approval gate on the same ground: **they are records, not decisions.**

## Why this shape

`governance.md` rule 2 stops code writing to `memory/` and `_config/`. These two are named exceptions, and the test each passes is that **nothing about a run changes because of what they contain** — for `caption-fixes.md`, the tally only *proposes*; for `boundary-tally.md`, no code path reads it back at all.

## Shape

**`memory/caption-fixes.md`** — a markdown table, read and rewritten whole by `learn_words.py:56-70,138-145`.
Columns: `Term (corrected to) | Was transcribed as | Count | Runs | Promoted`.
`Count` is **runs, not occurrences**. `Promoted` is what stops a term being proposed twice.
It is the only thing that remembers a word was wrong last month, which is why the threshold ("wrong in two separate runs") needs a file and not a variable.

**`memory/boundary-tally.md`** — three integers, written by `segment.py` (`TALLY` at `:54`, `_COUNTS` at `:55`, `keep_score()` at `:265`): videos processed, boundaries nominated, boundaries rejected. No per-run entries, nothing about any individual video.
It exists because printed output scrolls away, and it answers exactly one question: **has the loudness veto ever fired, or is it dead weight?** (`governance.md` rule 2, added 2026-08-14.) Delete it and the count restarts; nothing else changes.

Counted at `calibrate_audio.py:191`, after the file is written, so a run that fell over does not enter the count.

## Connected to

- **feeds** — [[lexicon]], through a proposal only
- **written by** — [[learn]] and [[calibrate]]
- **compared against** — [[audio-block]]'s `veto_review_after_videos: 10`, which only prints
- **looks like but is not** — [[preferences]], which is in `memory/` too but *does* change what a run does, and which code never writes.

## If you change this

**Hits**
- **Deleting `caption-fixes.md`** loses the across-runs count, so a word already corrected once starts from zero and needs two more runs to be proposed.
- **Editing the table by hand** works — `load_tally` parses it back — but the header above the table is preserved verbatim (`learn_words.py:138`) and the rows are rewritten sorted.
- **`memory/` is in `CHECK_DIRS`** (`tools/sync.py:34`), so editing either runs the fixture checks.

**Does not hit**
- **Any run's output.** That is the whole basis of the exemption. If a future change makes either file readable by a decision path, the exemption lapses and rule 2 applies again.
- **The lexicon.** Neither file writes it.

## Surfaces

Written by code, read by the person. `segment.py` run on its own writes nothing at all.

## See

`governance.md` rule 2 · `stages/04_learn/scripts/learn_words.py:56-70,138-146` · `stages/01b_calibrate/scripts/segment.py:254-292`
