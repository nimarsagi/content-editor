---
name: check
type: process
universe: live
status: verified
verified: 2026-08-26
consumes: [edit-defaults, audio-block, preferences]
produces: []
---

# Check

**Input →** whatever you just edited. **Movement →** compile it, then run the fixture end to end if it could change the outcome. **Output →** a tally line, or named failures.

```
python3 tools/sync.py                  both chores, over everything
python3 tools/sync.py path [path …]    only what those files affect
python3 tools/sync.py --quiet …        say nothing unless there is news
```

The `.claude/` hook runs the quiet form after every edit, passing the edited path (`.claude/hooks/after-edit.py:36-38`). It is a trigger, not the logic.

## Steps

1. `sync.py:106-115` — compile without importing, so nothing in the file runs. A syntax error surfaces the moment it is made rather than eight minutes into a render.
2. `sync.py:117-119` — **only if** the path is under `CHECK_DIRS` or in `CHECK_FILES`, and only if nothing failed to compile.
3. `run_checks` (`:73-92`) — build the fixture, run ~30 assertions, report the tally or the `FAIL` lines.

## The gap worth knowing

`tools/measure_audio.py` and `remotion/src/*` are both on the runtime path and in **neither** list, so editing them runs the syntax check only. `python3 tools/sync.py` with no arguments covers them. Details and the full assertion table in [[checks]].

## If you change this

**Hits**
- **A failing check never blocks an edit.** The hook always exits 0; the report arrives as text.
- **Widening the trigger lists** makes more edits pay the end-to-end render — the checks are sub-second, the render is not.

**Does not hit**
- **`output/`, `reference/`, `map/`, `BUILD-NOTES.md`** — edits there run neither chore.
- **Anything at runtime.** The fixture uses its own slug and its own 20-second video; a real run's folders are untouched.

## See

`tools/sync.py` · `tools/run_fixture_checks.py` · `.claude/hooks/after-edit.py`
