---
name: audio-block
type: object
cluster: dials
universe: live
status: verified
verified: 2026-08-26
---

# The audio block

`rules: audio:` in `_config/edit-defaults.yaml` — sixteen values governing how the voice is levelled. Its own card because the couplings between them are not visible from the file alone.

## Why this shape

**There is no target level, and that is the design.** The reference is the mean of the run's own per-segment levels, computed fresh every time (`edit-defaults.yaml:203-210`, `measure.py:207`). A fixed target is the one thing the measurements forbid: background level moved 12 dB between two of this person's videos.

Every number carries the measurement it came from, in `reference/source-specs/audio-measurements.md`. This card names only what moves together.

## Shape — what is coupled

**`scene_threshold` ↔ `min_step_db` ↔ `boundary_window_s`.** The picture nominates positions, loudness decides (`segment.py:85-107`). `min_step_db: 1.0` holds *because* a whole clip's voiced frames are averaged, collapsing uncertainty to ±0.35–0.61 dB. Lower `scene_threshold` from `0.05` toward `0.004` and spans drop to ~0.03 s, the margin collapses, and the check starts inventing boundaries — 393 nominations against 9 real cuts. **Neither may be changed without the other** (`edit-defaults.yaml:297-351`).

**`between_segment_correction` and `within_segment_correction` must stay separate** (`edit-defaults.yaml:268-270`). Both sit at `1.00`, set by the person on 2026-08-14. They protect different things, so tuning one by ear must not move the other.

**`within_segment_correction` is uncapped, knowingly.** `max_correction_db: 8.0` governs the between-segment offset only; the within-segment shift reached 10.29 dB on one video with nothing checking it. A cap was proposed at 12 and declined — a wrong correction is caught by ear on the next run.

**`drift_window_s: 1.5` is the first dial to reach for** if a finished video sounds worked-on. Raise it (`edit-defaults.yaml:436-447`, `apply_gain.py:29-35`).

**`min_drift_fit_s: 2.0` is why the start of a video may sound off.** Exactly one segment per video falls under it and goes uncorrected — on the reel, the opening 1.73 s, +3.6 dB out.

**`veto_review_after_videos: 10` is a review point, not a threshold.** Nothing acts on it; it only prints, against the count in [[tallies]].

## Connected to

- **part of** — [[edit-defaults]]
- **overridden by** — [[preferences]] § Audio, which is the *only* documented way to say "level it harder"
- **read by** — `measure.py:56` (`settings()`), then `segment.py`, `apply_gain.py`, `calibrate_audio.py`
- **produces** — [[levelled-audio]]
- **looks like but is not** — a CapCut clip setting. Three of the four operations cannot be expressed as one (`governance.md` rule 4).

## If you change this

**Hits**
- **Lowering `scene_threshold`** requires rethinking `min_step_db` in the same change. This is the one coupling that fails silently and audibly.
- **Any change re-runs the whole audio stage**, which is the slowest step. `segment.py [slug]` is the dry run — it writes nothing and prints the spread before and after.
- **`peak_ceiling_dbtp` is still open** — it is meant to be set by eye against CapCut's meter on one real export. `-1.0` is a starting value, not a finding.

**Does not hit**
- **The words, the cards, or the picture.** Nothing here is ever removed and no frame moves — `governance.md` rule 4, checked anyway by the sample-count assertion.
- **`caption.py --redo`**, which starts below this stage.
- **The boundaries agreeing with your CapCut cuts.** They are not meant to. A boundary is right when correcting across it evens the level out.

## Surfaces

Hand-edited by the person, by ear, on real output. Read by four scripts in `01b_calibrate`.

## See

`_config/edit-defaults.yaml:199-482` · `stages/01b_calibrate/CONTEXT.md` · `reference/source-specs/audio-measurements.md`
