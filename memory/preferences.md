# preferences.md — the overrides

**An override replaces one value in `_config/edit-defaults.yaml` for this deployment.** Write one here and the captions or the audio come out differently on the next run. **Every override carries its reason inline** — separating the two would undo the point: an override without its reason cannot be re-judged later, only obeyed or deleted.

**You write this file by hand.** Nothing proposes into it — the loop that used to is gone (`BUILD-NOTES.md`). What the tool still learns by itself is the *words*, and those go through `memory/caption-fixes.md` instead.

---

## How an override is written

```
### [what it governs] — [threshold or behaviour]
**Override:** raise `caption.min_duration_s` = 0.8
**Reason:** short cards flash by before I can read them.
**From:** output/runs/2026-08-03-pricing
```

The **Override** line is the only one the code reads, and what it does is replace that key's value in `_config/edit-defaults.yaml` for this deployment. Keep it mechanical: a backticked dotted key from that file, then `=`, then the value. Anything else in the line is prose for you, not for the code.

---

## Which components read this file

| Section | Read by | How |
|---|---|---|
| `## Pacing` | `chunk_captions.py` | overrides a value in `_config/edit-defaults.yaml` for this deployment — floor, ceiling, target window, line count |
| `## Audio` | `calibrate_audio.py` | overrides a value under `rules: audio:` in `_config/edit-defaults.yaml` — how far clips are levelled, how far drift is flattened, the ceiling, the filter |

**An override in a section nothing reads does nothing.** If you want to change something that fits under neither heading, the code needs extending first — a file that silently ignores half of what you write is the earlier failure repeating with more ceremony.

---

## Pacing

*(empty — no rules yet)*

---

## Audio

*(empty — no rules yet)*

**An audio override addresses the whole run, not one clip.** *"Level it harder than usual"* is one. *"Make the third clip quieter"* is not — the tool finds its own segments and they may differ between runs, so "the third clip" names nothing stable. If one clip ever genuinely needs rescuing on its own, that is the moment to add a way to say so; it has happened once in three videos.

**A key that matches nothing gets named out loud.** Mistype `audio.peak_ceiling_dbtp` and the run says so rather than ignoring you quietly. It does not stop — a typo is a typo, not a corrupted run — but it never passes in silence.

The two values most likely to want changing:

| Write this | To do this |
|---|---|
| `audio.between_segment_correction` = 0.9 | level the segments harder against each other (1.0 = perfectly flat) |
| `audio.within_segment_correction` = 0.7 | flatten more of the fade-off inside each segment (0 = leave it alone) |
