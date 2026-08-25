---
name: checks
type: object
cluster: engine
universe: live
status: verified
verified: 2026-08-26
---

# The checks

`tools/sync.py` — syntax, then the fixture checks. Run it after changing anything; the `.claude/` hook runs it for you.

## Why this shape

**The hook holds no logic.** It reads the edited path off the event and calls `sync.py --quiet <path>` (`.claude/hooks/after-edit.py:36-38`), so behaviour is identical whether it fires or you run it by hand. It always exits 0 — a chore failing is news, not a reason to block an edit already made.

**The fixture is a real 20-second video** built by `tools/make_fixture_video.py`, run end to end through the actual pipeline, and checked against `tools/fixtures/endtoend-truth.json`. Roughly 30 assertions across `run_fixture_checks.py:97-356`.

## Shape — what triggers the checks

`sync.py:33-36`:

```python
CHECK_DIRS  = {"stages", "_config", "memory"}
CHECK_FILES = {"pipeline_lib.py", "caption.py",
               "tools/make_fixture.py", "tools/run_fixture_checks.py"}
```

An edit outside both runs a **syntax check only**. `sync.py` with no arguments always runs everything.

### Two runtime files are outside that net

- **`tools/measure_audio.py`** is imported at runtime by `stages/01b_calibrate/scripts/measure.py:44` — it is not a dev tool. Editing it changes what the audio stage measures, and the fixture checks do not run.
- **`remotion/src/*`** is the renderer the end-to-end check exercises. Editing a component skips the checks too.

Neither is a bug in `sync.py` so much as a list that has not caught up with two later changes. `python3 tools/sync.py` with no arguments covers both.

### What the assertions actually guard

| Group | Line |
|---|---|
| the chain runs, a file exists at the end, and it is as long as the source | 118-156 |
| every spoken word reaches a caption; filler sounds are kept | 182-187 |
| duration ceiling, line count, character budget, ordering, no overlap | 189-233 |
| the safe margins, and that characters-per-line is derived not copied | 240-245 |
| audio: sample rate, channel count, sample count unchanged | 138-146 |
| boundary behaviour — kept on a join step, discarded with no step | 278-283 |
| **no model call sites** — a run costs transcription and nothing else | 318 |
| no runtime path opens the source specs; no script mentions Resolve | 324, 332 |
| the font is embedded, not fetched; no `delayRender()` at module scope | 345, 356 |

## Connected to

- **exercises** — [[run]] end to end, and therefore every artifact card
- **guards** — [[edit-defaults]]'s derived geometry, [[audio-block]]'s boundary logic, [[levelled-audio]]'s sample-count rule
- **looks like but is not** — `tools/render_smoke_test.py` and `tools/measure_audio.py`, neither of which `sync.py` invokes.

## If you change this

**Hits**
- **Adding a value to `_config/` that a check asserts** means updating `run_fixture_checks.py` in the same edit, or the check fails on the next save.
- **Widening `CHECK_DIRS`/`CHECK_FILES`** makes more edits pay the end-to-end render. The checks normally take under a second; the render is the slow part (`after-edit.py:42` allows 120 s).
- **The "no model call sites" check** is what keeps a run free. Adding a model call is a deliberate decision, and this assertion is where it surfaces.

**Does not hit**
- **A failing check does not block the edit.** The hook always exits 0; the report arrives as text.
- **`output/`, `map/`, `reference/`, `BUILD-NOTES.md`** — edits there run neither chore.

## Surfaces

Run by the hook after every edit, and by hand. Reports to the console and, via the hook, into the assistant's context.

## See

`tools/sync.py` · `tools/run_fixture_checks.py` · `.claude/hooks/after-edit.py`
