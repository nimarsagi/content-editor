---
name: run-folder
type: object
cluster: artifacts
universe: live
status: verified
verified: 2026-08-26
---

# Run folder

`output/runs/[YYYY-MM-DD-slug]/` — one run's entire trail. The slug is the primary key of the whole system: it is the only argument every stage script takes.

## Why this shape

**Status is derivable by looking.** There is no run database and no state field — which files exist in the folder says how far the run got. Filenames carry the stage number that produced them (`01-`, `02-`, `03-`, `04-`) so the trail reads in order rather than alphabetically.

The slug is `date + slugified topic`, capped at 40 characters (`caption.py:72-74`, `caption.py:149`). It is derived from the topic rather than asked for, because a run you have to name is a form to fill in.

## Shape

| File | Written by | Hand-editable |
|---|---|---|
| `01-topic.md` | `caption.py:151` | — |
| `01-video.md` | `read_video.py:71` | **yes** → [[video-record]] |
| `01-transcript.json` | `transcribe.py:136` | **yes** → [[transcript]] |
| `01-transcript-raw.json` | `transcribe.py:146` | **never** |
| `02-caption-cards.json` | `chunk_captions.py:411` | yes → [[caption-cards]] |
| `02-captions.srt` | `write_srt.py` | yes |
| `03-remotion-props.json` | `render_captions.py:236` | — → [[remotion-props]] |
| `04-proposed-words.md` | `learn_words.py:163` | **approval gate** — ghost, never yet produced |

`01b_calibrate` writes **nothing** here, deliberately — the trace is the levelled file and what it printed (`stages/01b_calibrate/CONTEXT.md`, "This stage leaves no trail file").

## Connected to

- **owns** — [[video-record]], [[transcript]], [[caption-cards]], [[remotion-props]]
- **owned by** — nothing; `output/` is untracked and safe to clear
- **looks like but is not** — [[levelled-audio]], which lives in `output/audio/[slug]/` under the same slug but is not part of this folder and is cleared separately

## If you change this

**Hits**
- **Adding a file to a run** means picking a stage-number prefix, and `01b_calibrate`'s absence from this table is a decision on record — re-read that contract before adding one for it.
- **Renaming any file here** hits `caption.py`, the stage that writes it, every stage that reads it, `tools/run_fixture_checks.py`, and every existing run folder on disk.
- **Renumbering a stage** is why `01b` exists rather than a renumbered `02` (`stages/01b_calibrate/CONTEXT.md`, "Why it is `01b`").

**Does not hit**
- The finished video. That goes to `paths.yaml`'s `render_output`, outside the workspace — see [[paths]].
- `git`. `output/` is ignored; nothing here is ever committed.

## Surfaces

Written by every stage. Read by the person, by hand, between runs. `lib.run_dir()` (`pipeline_lib.py:163`) is the only thing that resolves the path.

## See

`pipeline_lib.py:163-170` · `caption.py:126-156` · root `CLAUDE.md`, "The run folder"
