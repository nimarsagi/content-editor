# Every noun in this workspace

One line each. Open the card, not the folder.

## artifacts/ — what a run produces

| Noun | Is | Card |
|---|---|---|
| **run folder** | `output/runs/[slug]/`, one run's whole trail | [run-folder](artifacts/run-folder.md) · live · verified |
| **video record** | `01-video.md` — the original export's path, duration, fps | [video-record](artifacts/video-record.md) · live · verified |
| **transcript** | `01-transcript.json` (yours) + `-raw.json` (write-once) | [transcript](artifacts/transcript.md) · live · verified |
| **caption cards** | `02-caption-cards.json` + the `.srt` sidecar | [caption-cards](artifacts/caption-cards.md) · live · verified |
| **levelled audio** | `output/audio/[slug]/…-levelled.mov`, deletable | [levelled-audio](artifacts/levelled-audio.md) · live · verified |
| **Remotion props** | `03-remotion-props.json` — exactly what the renderer got | [remotion-props](artifacts/remotion-props.md) · live · verified |
| **word proposal** | `04-proposed-words.md` — the lexicon approval gate | [lexicon](dials/lexicon.md) · **ghost** — documented, never yet produced |

## dials/ — what a change targets

| Noun | Is | Card |
|---|---|---|
| **edit defaults** | `_config/edit-defaults.yaml` — the rules/diagnostics split | [edit-defaults](dials/edit-defaults.md) · live · verified |
| **the audio block** | `rules: audio:` — the levelling dials and their couplings | [audio-block](dials/audio-block.md) · live · verified |
| **lexicon** | `_config/lexicon.txt` — terms that seed transcription | [lexicon](dials/lexicon.md) · live · verified |
| **preferences** | `memory/preferences.md` — per-deployment overrides | [preferences](dials/preferences.md) · live · verified |
| **paths** | `_config/paths.yaml` — the only two paths in the workspace | [paths](dials/paths.md) · live · verified |
| **tallies** | `caption-fixes.md`, `boundary-tally.md` — records, not decisions | [tallies](dials/tallies.md) · live · verified |

## engine/ — how it is wired

| Noun | Is | Card |
|---|---|---|
| **pipeline lib** | `pipeline_lib.py` — config loading, run paths, ffprobe | [pipeline-lib](engine/pipeline-lib.md) · live · verified |
| **step list** | `caption.py`'s `STEPS` and `REDO_FROM` | [step-list](engine/step-list.md) · live · verified |
| **the checks** | `tools/sync.py`, `run_fixture_checks.py`, the edit hook | [checks](engine/checks.md) · live · verified |

## Ghosts — named, not wired

Do not assume changing one of these changes anything. Details in [edit-defaults](dials/edit-defaults.md).

- **14 config keys no code reads**, including `resolution`, `safe_zone`, `single_export_serves`, `caption_motion`, `lead_in_s`, `gap_between_cards_s`, `prefer_fewest_cards`, `preserve_quotes`, `allow_orphan_cards`
- **`04-proposed-words.md`** — the approval gate exists in code and has never fired
- **six deleted scripts** still present as `__pycache__/*.pyc`: `join_session`, `apply_cuts`, `build_timeline`, `render`, `maintain_lexicon`, `read_markers` — leftovers of the Resolve/cut-proposal era (`BUILD-NOTES.md`)
