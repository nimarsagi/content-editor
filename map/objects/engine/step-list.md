---
name: step-list
type: object
cluster: engine
universe: live
status: verified
verified: 2026-08-26
---

# Step list

`STEPS` and `REDO_FROM` in `caption.py:45-66` — the pipeline's actual order, and the boundary that makes `--redo` safe.

## Why this shape

**The order is the folder numbering, written once.** Six scripts, run as subprocesses in sequence; the run stops at the first non-zero exit (`caption.py:158-165`).

**`REDO_FROM = 3` is derived from the step list, not written out a second time.** The boundary is "everything that reads the transcript, nothing that writes it" — the whole safety of the feature, so it is a slice index rather than a duplicated list (`caption.py:54-57`).

**It moved from 2 to 3 when calibration was inserted, in the same change.** Levelling needs word timings so it cannot sit above `transcribe.py`, and slotting it below put it exactly where the boundary pointed — which would have made every `--redo` re-process a finished file. Calibration refuses its own output as a backstop; with the boundary here that refusal should never fire in normal use, and a safety rule that trips during ordinary work is one that gets switched off (`caption.py:58-65`).

## Shape

```
1  01_ingest/read_video.py          ← the only step given the video path
2  01_ingest/transcribe.py
──────────────────────────────────  REDO_FROM = 3
3  01b_calibrate/calibrate_audio.py
4  02_assemble/chunk_captions.py
5  02_assemble/write_srt.py
6  03_render/render_captions.py
```

`04_learn` is **not in the list**. It is not part of a run; nothing waits for it (`CONTEXT.md`, "04_learn is not part of a run").

Every script takes the slug as `argv[1]`; only `read_video` also gets the video (`caption.py:160-162`).

## Connected to

- **drives** — [[run]] and [[redo]]
- **writes** — `01-topic.md`, and creates the [[run-folder]]
- **looks like but is not** — the stage folder numbering. `01b` exists so this list could gain a step without renumbering anything (`stages/01b_calibrate/CONTEXT.md`).

## If you change this

**Hits**
- **Inserting a step below index 3 shifts `REDO_FROM`'s meaning.** The slice is positional: a step added at position 3 becomes the first thing `--redo` runs. Check which side of the transcript-write boundary it falls on.
- **Adding a step that needs an argument other than the slug** means touching `caption.py:160-162`, which special-cases `read_video` by name.
- **`caption.py` is in `CHECK_FILES`** (`tools/sync.py:35`) — an edit runs the fixture checks, including the full end-to-end render.

**Does not hit**
- **The stage contracts.** Each `stages/*/CONTEXT.md` describes its own step and is not read by code.
- **Running a stage by hand.** Every script works standalone with a slug — that is how the audio dials get tuned.

## Surfaces

Read by nothing but `caption.py` itself. The one place the pipeline's order exists as data.

## See

`caption.py:45-66,158-165` · `CONTEXT.md`
