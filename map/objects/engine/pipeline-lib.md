---
name: pipeline-lib
type: object
cluster: engine
universe: live
status: verified
verified: 2026-08-26
---

# Pipeline lib

`pipeline_lib.py` — the shared plumbing every stage imports. Config loading, preference overrides, run-folder paths, ffprobe, JSON I/O.

## Why this shape

**Engine, not a stage.** It holds no threshold and no path of its own — it only reads `_config/`. The one rule it enforces on callers: a stage reads a value from config or preferences, never from a literal in its own source (`pipeline_lib.py:1-10`).

Constants are **derived, not restated**. `RUNS_REL` (`:37`) is computed from `RUNS_DIR` so moving the folder is one line — the docstring names `caption.py`'s step list as the standing example of what a second copy costs.

## Shape

| Group | Functions | Line |
|---|---|---|
| paths | `ROOT`, `CONFIG_DIR`, `MEMORY_DIR`, `OUTPUT_DIR`, `RUNS_DIR`, `RUNS_REL` | 21-37 |
| config | `load_config`, `rules`, `diagnostics`, `load_paths`, `load_lexicon` | 54-93 |
| overrides | `load_preferences`, `apply_overrides` | 103-157 |
| run folder | `run_dir`, `read_json`, `write_json`, `require` | 163-192 |
| media | `probe_duration`, `probe_frame_rate`, `probe_codec`, `probe_audio` | 198-313 |
| output | `timecode` | 316 |

`load_config` exits if the `rules`/`diagnostics` split is gone (`:59-66`) — the only structural assertion made at import time.

Every stage reaches it the same way: `sys.path.insert(0, parents[3])` then `import pipeline_lib as lib`.

## Connected to

- **reads** — [[edit-defaults]], [[paths]], [[lexicon]], [[preferences]]
- **owns** — the [[run-folder]] path convention
- **imported by** — every script in `stages/` and `tools/`
- **looks like but is not** — `stages/01_ingest/scripts/read_video.py`, which also exports a shared helper (`read_record`) that three other stages import across stage folders. That is the one cross-stage import that does not go through this file.

## If you change this

**Hits**
- **Every stage at once.** It is in `CHECK_FILES` (`tools/sync.py:35`), so an edit always runs the fixture checks.
- **`probe_frame_rate` divides the fraction and never rounds** (`:214-241`) — the six-decimal frame rate depends on it.
- **`probe_audio` returns `{}` for a file with no audio stream** (`:296-297`), so a caller can tell "silent" from "different". Callers rely on the empty-dict case (`calibrate_audio.py:164`).

**Does not hit**
- **The Remotion side**, which imports nothing from Python.
- **Values.** Adding a threshold here would break the file's own rule; it belongs in `_config/`.

## Surfaces

Imported by everything. Never run directly. Never hand-edited during a run.

## See

`pipeline_lib.py`
