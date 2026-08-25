---
name: transcript
type: object
cluster: artifacts
universe: live
status: verified
verified: 2026-08-26
---

# Transcript

Two files with the same shape and opposite rules. `01-transcript.json` is **yours** — the edit surface where a misheard word gets fixed. `01-transcript-raw.json` is written once and never again.

## Why this shape

**The pair is what makes learning possible at all.** A correction is only visible as a correction if something remembers what was there before. Overwrite the raw file and `learn_words.py` sees a clean transcript, tallies nothing, and the lexicon never grows — silently, with everything still appearing to work (`governance.md` rule 3).

`transcribe.py:141-147` refuses to replace the raw file if it exists and says so. That refusal, plus `REDO_FROM` skipping transcription (see [[step-list]]), is the whole safety of the fix-a-word loop.

Word-level timings are non-negotiable (`transcribe.py:103`); the run aborts by name if the model returns segment-level timing only (`transcribe.py:112-117`).

## Shape

`transcribe.py:129-135` — `topic`, `video`, `duration`, `fps`, `words[]`.
Each word: `word`, `start`, `end`, `probability` (`transcribe.py:119-124`).

**The `"video"` field is not stable.** `transcribe.py` writes the original path; `calibrate_audio.py:195` overwrites it with [[levelled-audio]]. After one run it points at the levelled copy, which is why nothing may treat it as the original — [[video-record]] holds that.

## Connected to

- **owned by** — [[run-folder]]
- **produced by** — [[run]] step 2
- **read by** — `calibrate_audio.py:98` (word spans, to find speech), `chunk_captions.py:286`, `render_captions.py:53`, `learn_words.py:87-88`
- **looks like but is not** — the raw copy. `chunk_captions.py:283-285` deliberately does *not* read it.

## If you change this

**Hits**
- **Editing a word** changes the cards, the `.srt`, the burned-in video, and what `learn_words.py` tallies. `caption.py --redo [slug]` rebuilds all of it.
- **Adding or deleting a word** (rather than substituting in place) puts every position after it out of step and `learn_words.py:94-99` stops and tallies nothing. It is not an error, but the run teaches nothing.
- **Changing the field names** hits four scripts and the fixture truth file `tools/fixtures/endtoend-truth.json`.

**Does not hit**
- **The audio.** `caption.py --redo` starts below calibration (`caption.py:66`), so a spelling fix never re-levels the file — deliberate, since it would produce an identical file at the cost of the slowest step.
- **The lexicon.** Fixing a word proposes nothing until it has been wrong in two separate runs, and even then it only writes a proposal — see [[lexicon]].

## Surfaces

Written by `transcribe.py`; the `"video"` field rewritten by `calibrate_audio.py`. Read by four scripts. Hand-edited by the person — the corrected file is the point.

## See

`stages/01_ingest/scripts/transcribe.py:129-147` · `governance.md` rule 3 · `stages/04_learn/CONTEXT.md`
