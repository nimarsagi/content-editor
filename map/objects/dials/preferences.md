---
name: preferences
type: object
cluster: dials
universe: live
status: verified
verified: 2026-08-26
---

# Preferences

`memory/preferences.md` — hand-written overrides that replace one value in `_config/edit-defaults.yaml` for this deployment.

## Why this shape

**Only one line per rule is machine-read**, and everything else is prose for the person:

```
**Override:** raise `caption.min_duration_s` = 0.8
```

`_OVERRIDE_LINE` (`pipeline_lib.py:99`) finds the line; `_OVERRIDE` (`:100`) pulls a backticked dotted key and a numeric value. Anything non-numeric comes back as text nothing reads. Keeping the reason inline is deliberate — an override without its reason can only be obeyed or deleted, never re-judged.

**A key matching nothing is named out loud, not silently ignored** (`pipeline_lib.py:146,153`; audio keys additionally at `calibrate_audio.py:86-88`). The run carries on — a typo is a typo, not a corrupted run.

## Shape

Sections are `## `-headed and matched by exact name (`pipeline_lib.py:122-127`). **Two sections are read. No others exist:**

| Section | Read by |
|---|---|
| `## Pacing` | `chunk_captions.py:292` |
| `## Audio` | `calibrate_audio.py:86` |

**An override under any other heading does nothing, silently.** The file says so itself, and that warning is the load-bearing part of it.

Both sections are currently empty.

## Connected to

- **overrides** — [[edit-defaults]], one dotted key at a time, via `apply_overrides` (`pipeline_lib.py:139-157`)
- **recorded in** — [[caption-cards]], as `pacing_overrides`
- **looks like but is not** — [[tallies]]. Both live in `memory/`, but this one changes what a run does and the tallies do not. It is also **exempt from nothing**: `governance.md` rule 2 covers writes by code, and nothing proposes into this file any more.

## If you change this

**Hits**
- **A `## Pacing` override re-chunks every card** on the next run and is stamped into the cards file.
- **An `## Audio` override changes the levelling** for the whole run — never for one clip. "The third clip" names nothing stable, since segments are the tool's own and may differ between runs.
- **`memory/` is in `CHECK_DIRS`** (`tools/sync.py:34`) — precisely because an override's whole job is to change the output.

**Does not hit**
- **Anything under a third heading.** Adding `## Typography` here and writing overrides into it changes nothing, and nothing will warn you — the warning only fires for a key that is read and does not resolve.
- **Non-numeric values.** `_OVERRIDE` matches `[-\d.]+` only; `= none` or `= true` is prose.

## Surfaces

Written by hand, by the person, only. Read by two stages.

## See

`memory/preferences.md` · `pipeline_lib.py:96-157` · `governance.md` rule 2
