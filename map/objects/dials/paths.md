---
name: paths
type: object
cluster: dials
universe: live
status: verified
verified: 2026-08-26
---

# Paths

`_config/paths.yaml` — the only place a filesystem path may appear in this workspace. Two keys.

## Why this shape

Everything outside `_config/` is the reusable engine; `_config/` holds what changes if someone else deployed this. A path in a script would tie the engine to one machine.

## Shape

| Key | Where it points | Absolute? |
|---|---|---|
| `render_output` | `~/Movies/content-editor-renders` — the finished, post-able file | yes, outside the workspace |
| `audio_output` | `output/audio` — [[levelled-audio]], working material | relative to the workspace |

The split is deliberate: one is the thing you post, the other is cleared without ceremony. `calibrate_audio.py:54-57` resolves a relative `audio_output` against the workspace root; `render_captions.py:238` expands `render_output` and creates it.

Everything else derives from `pipeline_lib.py:21-37`: `ROOT`, `CONFIG_DIR`, `MEMORY_DIR`, `OUTPUT_DIR`, `RUNS_DIR`, and `RUNS_REL` — the console-facing string, derived rather than typed at each print site.

## Connected to

- **owns** — [[levelled-audio]] and the render output
- **read by** — `render_captions.py:238`, `calibrate_audio.py:48`
- **looks like but is not** — `pipeline_lib`'s constants, which are structural (where `output/` sits relative to the code) rather than deployment settings. Those live in code on purpose.

## If you change this

**Hits**
- **Moving `audio_output`** changes what `refuse_own_output` recognises as this stage's own work (`calibrate_audio.py:62-76`). The refusal is purely locational, so pointing it at a folder your sources live in would defeat it.
- **Removing `audio_output`** stops the audio stage with a named error (`calibrate_audio.py:49-53`).
- **Moving `render_output`** changes only where the finished file lands; the folder is created if missing.

**Does not hit**
- **`output/runs/`**, which is not configurable — it is `pipeline_lib.py:32-33`.
- **`input/`**, likewise fixed, at `caption.py:88`.
- **Existing runs.** Nothing rewrites a path already recorded in a transcript or a video record.

## Surfaces

Hand-edited by the person on deployment. Read by two scripts.

## See

`_config/paths.yaml` · `pipeline_lib.py:21-37` · root `CLAUDE.md`, "Engine vs config"
