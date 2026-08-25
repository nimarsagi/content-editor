---
name: levelled-audio
type: object
cluster: artifacts
universe: live
status: verified
verified: 2026-08-26
---

# Levelled audio

`output/audio/[slug]/[name]-levelled[.ext]` — a full-size copy of the export with the voice evened out. Picture untouched, nothing removed.

## Why this shape

**It is meant to be deletable.** It fills with full-size video and is git-ignored, so it will get cleared — and `render_captions.py:56-72` falls back to the original from [[video-record]] when it is gone, printing why. That fallback is the reason the original path is recorded in a separate file at all.

**The stage refuses its own output**, recognised by location: a source path sitting inside `audio_output` is this stage's own work (`calibrate_audio.py:62-76`). No marker in the file, no filename convention, nothing to keep in sync. It stops the run rather than skipping — a skipped step produces a file that looks finished and is not.

## Shape

One file per run, named from the source stem plus `-levelled` (`calibrate_audio.py:183`). Written by `apply_gain.write()` and immediately checked by `apply_gain.verify()` (`calibrate_audio.py:184-185`).

Three checks stop the run: same sample count out as in, audio still starts with the picture, same rate and channel count (`stages/01b_calibrate/CONTEXT.md`, "Three self-checks").

## Connected to

- **owned by** — `_config/paths.yaml` → `audio_output`, see [[paths]]
- **pointed at by** — [[transcript]]'s `"video"` field, rewritten at `calibrate_audio.py:195`
- **produced by** — [[calibrate]]
- **looks like but is not** — the finished post-able file. That is Remotion's output in `render_output`, a different path entirely.
- **looks like but is not** — [[run-folder]]. Same slug, different tree, cleared separately.

## If you change this

**Hits**
- **Deleting it** costs nothing: the render falls back to the original and says so. Re-run `calibrate_audio.py [slug]` to get it back.
- **Moving `audio_output`** changes what `refuse_own_output` recognises. The refusal is purely locational — point it somewhere the source lives and the stage would process its own output.
- **Re-running calibration** overwrites the previous output from the same source, which is what makes tuning the correction amounts by ear practical: change a value, run, listen.

**Does not hit**
- **The caption timings.** The levelled file has the same duration and sample count by construction; the words were timed against the original and still line up.
- **`caption.py --redo`**, which starts below this stage (`caption.py:66`).

## Surfaces

Written by `calibrate_audio.py`. Read by `render_captions.py` via the transcript's `"video"` field. Listened to by the person — that is the only real check on it.

## See

`stages/01b_calibrate/scripts/calibrate_audio.py:46-76,183-196` · `stages/01b_calibrate/CONTEXT.md`
