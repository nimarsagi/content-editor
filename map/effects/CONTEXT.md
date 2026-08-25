# If you are changing X, open these

A catalog, not a waterfall. It says which cards to read before a change; the cards hold the reasoning. **If this page and a card disagree, the card is right** — fix the card, then fix this line.

---

## Captions

| Changing… | Open | The thing people get wrong |
|---|---|---|
| **font size, `max_lines`, line width** | [edit-defaults](../objects/dials/edit-defaults.md), [caption-cards](../objects/artifacts/caption-cards.md) | These three move together, and the character budget is **re-derived at runtime**. Re-run `chunk_captions.py` — a re-render alone keeps the old line breaks. |
| **a duration threshold** | [edit-defaults](../objects/dials/edit-defaults.md), [caption-cards](../objects/artifacts/caption-cards.md) | Duration is the only enforceable rule. Word count and reading speed are diagnostics and cannot be promoted — captions track speech at zero gap. |
| **the split logic** | [caption-cards](../objects/artifacts/caption-cards.md) | `wrap()` returning `None` means *close the card earlier*, never *slice the string*. |
| **the caption style** | [remotion-props](../objects/artifacts/remotion-props.md) | Three edits in step: the props builder, `types.ts`, the component. `lineHeightEm` is hardcoded in **two** places. |
| **the frame size** | [edit-defaults](../objects/dials/edit-defaults.md) | `geometry.canvas` is what renders. `render.resolution` is read by nothing. |

## Audio

| Changing… | Open | The thing people get wrong |
|---|---|---|
| **`scene_threshold`** | [audio-block](../objects/dials/audio-block.md) | Never alone — `min_step_db`'s margin depends on it. Lowering it makes the stage invent boundaries. |
| **how hard it levels** | [audio-block](../objects/dials/audio-block.md), [calibrate](../processes/calibrate.md) | Two separate corrections that must stay separate. Tune by ear: change, run, listen. |
| **"it sounds processed"** | [audio-block](../objects/dials/audio-block.md) | Raise `drift_window_s` first. |
| **"the start sounds off"** | [audio-block](../objects/dials/audio-block.md) | `min_drift_fit_s` — one segment per video goes uncorrected under it, usually the opening. |
| **anything in `01b_calibrate`** | [calibrate](../processes/calibrate.md), [levelled-audio](../objects/artifacts/levelled-audio.md) | Nothing may be removed. The sample-count check stops the run. |

## Files and wiring

| Changing… | Open | The thing people get wrong |
|---|---|---|
| **adding or reordering a stage** | [step-list](../objects/engine/step-list.md), [run-folder](../objects/artifacts/run-folder.md) | Check which side of `REDO_FROM` it lands on. Use a letter suffix rather than renumbering. |
| **a run-folder filename** | [run-folder](../objects/artifacts/run-folder.md) | Hits the writer, every reader, the fixture checks, and every run already on disk. |
| **where files are written** | [paths](../objects/dials/paths.md) | `audio_output` is also what the refuse-own-output check matches on. |
| **the transcript schema** | [transcript](../objects/artifacts/transcript.md) | Four scripts plus `tools/fixtures/endtoend-truth.json`. |
| **shared plumbing** | [pipeline-lib](../objects/engine/pipeline-lib.md) | It may not hold a threshold or a path. That is the rule it exists to enforce. |
| **`tools/measure_audio.py`** | [checks](../objects/engine/checks.md) | It is **runtime code**, imported by the audio stage — and editing it does **not** trigger the fixture checks. |
| **anything in `remotion/`** | [checks](../objects/engine/checks.md), [remotion-props](../objects/artifacts/remotion-props.md) | Same gap: run `python3 tools/sync.py` with no arguments. |

## Rules and learning

| Changing… | Open | The thing people get wrong |
|---|---|---|
| **adding a model call** | [checks](../objects/engine/checks.md) | `run_fixture_checks.py:318` asserts there are none. That is a deliberate decision, not an obstacle to route around. |
| **the lexicon** | [lexicon](../objects/dials/lexicon.md) | Code proposes; only a person writes. A wrong entry biases every future transcription. |
| **an override** | [preferences](../objects/dials/preferences.md) | **Only `## Pacing` and `## Audio` are read.** An override under any other heading does nothing, silently. |
| **writing to `memory/`** | [tallies](../objects/dials/tallies.md) | The two exemptions hold only while nothing reads those files back into a decision. |
| **restoring the cut-proposal loop** | — | Read *What changed on 2026-07-29* in `BUILD-NOTES.md` first. The loop has nowhere to send proposals: CapCut has no scripting interface. |
