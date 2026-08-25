# map/ — the edit map for this workspace

Two questions, answered without reading the whole tree: **what is X**, and **what else moves if I change X**.

This is not a second spec. The workspace is the source of truth and every card cites it by path and line. Where a card and the code disagree, the code wins and the card is stale.

---

## Where to go

| You are about to… | Open |
|---|---|
| change a threshold, a size, a path | `effects/CONTEXT.md` — then the card it names |
| understand a file a run produces | `objects/artifacts/` |
| understand a value in `_config/` or `memory/` | `objects/dials/` |
| change how stages are wired, shared, or checked | `objects/engine/` |
| follow one movement start to finish | `processes/` |
| look up any noun by name | `objects/_index.md` |

**Do not read `objects/` as a folder.** Open the index, then the one card. The index exists so you do not have to.

To *run* the pipeline, none of this applies — the root `CLAUDE.md` has the command and nothing here is consulted during a run.

---

## Words that mean two things

| Word | Sense A | Sense B |
|---|---|---|
| **cut** | what you removed in CapCut, before the file arrived | an audio **segment boundary** — a place the gain changes, removing nothing (`governance.md` rule 4) |
| **clip** | one file off the phone; invisible once exported | a **segment** the audio stage found by measuring. Three segments in a nine-clip video is the stage working |
| **animation** | your separate, unstarted project of drawing visuals into videos | *not* used for captions — the config key is `caption_motion` on purpose, so deleting one never deletes the other |
| **transcript** | `01-transcript.json`, yours, an edit surface | `01-transcript-raw.json`, write-once, the only record of what the model heard |
| **the video** | `01-video.md` → the original export, survives a clear-out | `01-transcript.json`'s `"video"` field → the *levelled copy*, repointed by the audio stage |
| **rule** | one of `governance.md`'s four design invariants | the `rules:` block in `edit-defaults.yaml` — values whose violation is a bug |
| **measure** | `stages/01b_calibrate/scripts/measure.py`, levels per span | `tools/measure_audio.py`, levels per file — and the first **imports** the second |

---

## How to read a card

`CONTEXT.md` has the layout, the three universes (live / leftover / ghost), and the date every card was verified against.
