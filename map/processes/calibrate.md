---
name: calibrate
type: process
universe: live
status: verified
verified: 2026-08-26
consumes: [video-record, transcript, audio-block, preferences, paths]
produces: [levelled-audio, tallies]
---

# Calibrate

**Input →** the original export plus the word timings. **Movement →** measure the speech, find where the level steps, correct twice, cap the peaks. **Output →** [[levelled-audio]], and the transcript's `"video"` field repointed at it.

```
python3 stages/01b_calibrate/scripts/segment.py <slug>   dry run — writes nothing
python3 stages/01b_calibrate/scripts/measure.py <slug>   the levels, nothing else
python3 stages/01b_calibrate/scripts/calibrate_audio.py <slug>
```

## Steps

1. `calibrate_audio.py:85-88` — load [[audio-block]]; name any override key that resolves to nothing.
2. `calibrate_audio.py:90-96` — source from [[video-record]], **never** from the transcript's `"video"` field, which this stage overwrites. Then refuse the source if it sits inside `audio_output`.
3. `segment.find` (`calibrate_audio.py:108`) — **the picture nominates, loudness decides.** Scene scores propose positions; a boundary survives on the **larger of two measurements** — the step at the join, and the step between whole segments. Each catches what the other cannot.
4. `calibrate_audio.py:126-134` — per word: the segment's offset plus `apply_gain.flatten`'s within-segment shift.
5. `calibrate_audio.py:143-158` — report two ways, labelled: the spread of the segment averages (improves by construction) and second-by-second steadiness (moves only when the video does).
6. `calibrate_audio.py:168-185` — high-pass, gain envelope, limiter, write, verify.
7. `calibrate_audio.py:191-196` — tally, then repoint the transcript.

**Steps 4's two corrections cannot swap.** Correcting drift changes a segment's average unless done around that average.

## The tune-by-ear loop

Re-running overwrites the previous output from the same source, so: change a value in [[audio-block]], run, listen. `drift_window_s` is the first dial to reach for if the result sounds worked-on. That loop is why the two correction amounts are described in config as tuning values rather than findings.

## If you change this

**Hits**
- **`scene_threshold` and `min_step_db` are coupled** and must move together — the one change here that fails silently and audibly.
- **Moving `audio_output`** changes what the refuse-own-output check recognises. See [[paths]].
- **`stages/` is in `CHECK_DIRS`**, so any edit runs the end-to-end fixture, including the boundary assertions at `run_fixture_checks.py:278-309`.

**Does not hit**
- **The picture, the words, or the length.** Nothing is removed; the sample-count check stops the run otherwise (`governance.md` rule 4).
- **The run folder.** This stage writes no trail file, deliberately — the trace is the levelled file, the repointed field, and what it printed.
- **`caption.py --redo`.** It starts below this stage.

## See

`stages/01b_calibrate/scripts/calibrate_audio.py` · `stages/01b_calibrate/CONTEXT.md` · `governance.md` rule 4
