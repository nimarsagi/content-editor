# 01b_calibrate — stage contract

**Takes** the finished export and the transcript of it.
**Gives back** a copy of that export whose voice holds a steady level — clip to clip and start-to-end inside a clip — without reaching the top of the meter.

*One finished video in, the same video out with the audio evened up. Nothing is removed, nothing is re-encoded, nothing about the picture changes.*

---

## Why it is `01b` and not `02`

It runs after transcribing and before caption cards, so it needs a number between the two. Renumbering the later stages would rewrite paths across `caption.py`, the check script, the docs and every existing run folder's file prefixes — moving working code, which is the thing this shape was chosen to avoid. `01b` slots in without touching a single existing name.

---

## Inputs

| Input | Level | Notes |
|---|---|---|
| the finished export | **L4 — this run** | its path comes from `01-video.md`, via `read_record()` — **never** from the `"video"` field in the transcript, which this stage overwrites |
| `01-transcript.json` | **L4 — this run** | word spans only. Levels are measured on speech, and this is what says where speech is |
| `_config/edit-defaults.yaml` → `rules: audio:` | L3 — stable | every threshold. No script here holds a number |
| `memory/preferences.md` → `## Audio` | L3 — stable | overrides any of those, for this run |

## Outputs

| What | Where | Notes |
|---|---|---|
| the levelled video | `output/audio/[run]/` | full-size, git-ignored, **safe to delete** — the renderer falls back to the original when it is gone |
| the `"video"` field | `01-transcript.json` | repointed at the levelled copy, so the renderer picks it up |
| the flags | printed with the run | **nothing is written into the run folder** — see below |
| three running totals | `memory/boundary-tally.md` | videos processed, boundaries nominated, boundaries rejected. Not per-run, not about any video |

**This stage leaves no trail file, and that is a deliberate break with the run-folder convention.** Every other stage writes something into `output/runs/[slug]/`. A per-run document listing what the tool was unsure about is a change log under another name, and a change log was declined outright: *"I don't need a change log. I can hear myself whether it did a good job or not."* Confirmed again when the break was put directly: *"I dont need to see what happened, just the output suffices."* The trace is the levelled file, the updated field, and what it said while running. The accepted cost is that printed output scrolls away, so there is no history of what past runs flagged.

**The one exception is three integers, and it exists because that cost bit** (2026-08-14). `memory/boundary-tally.md` counts videos processed, boundaries nominated and boundaries rejected by the loudness check — across all runs, with no per-run entries and nothing about any individual video. It answers one question a printed line cannot: whether the loudness veto has *ever* fired, or is dead weight kept on faith. Nothing reads it back. `segment.py` run on its own still writes nothing at all.

---

## The order of operations, which is load-bearing

1. **High-pass at ~80 Hz** — always, and *first*, so no level is ever computed with rumble in it and the same filter serves both the measurement and the delivered file.
2. **Segment** — the picture nominates positions, measured loudness decides.
3. **Hold the level steady inside each segment**, around that segment's own mean — by following the level over `drift_window_s` of audio, not by fitting a line to it.
4. **Move each segment toward the run's average.**
5. **Cap the peaks.**
6. **Mux, copying the picture untouched**, then check the result.

**Three and four cannot swap.** Correcting inside a segment changes its average unless it is done around that average — so if the between-segment offset were applied first, step three would move every clip against the reference just measured.

**Three follows the level; it does not fit a line to it** (2026-08-14). A line can only remove a tilt, and the level inside a clip does not tilt — it humps. After the boundary fix the reel still had eleven seconds sitting more than 3 dB from its own average, reported as *"some parts are significantly louder than others."* Following the level took that to three, and the seconds more than 5 dB out from four to none. **The level is read from a window of audio, never from per-word medians** — 26 of 216 words on the reel carry fewer than five voiced frames, and within two seconds the per-word figures run from `-11.4 dB` on *"this"* to `-51.7 dB` on *"is"*, which is measurement noise rather than the voice.

**Five is never done by turning a clip down.** Lowering whole-clip gain until the loudest consonant clears the meter makes the clip quiet and lands every clip at a different level, which is the problem this stage exists to solve. The ceiling is enforced at the peak itself.

---

## Four rules this stage exists to hold

### Divide to treat, never to delete

Two different things share the word "cut". **Dividing** the audio so each part can be treated separately is how this stage works at all. **Deleting** any span of audio is never allowed, for any reason, in any build. Nothing leaves the file: a boundary is a place where the treatment changes, not a place where something is taken out.

This is what protects the words. Divide as finely as the levelling needs and no word can be lost, because nothing is ever removed. It holds by construction rather than by a runtime check — and the length check below catches it anyway if it ever stopped holding.

### Segmenting is not editing — the person owns the cut

*"Whatever you cut is based purely on averaging out the audio. Not content."* The boundaries here are the places the gain is allowed to change and nothing else. They never move a frame of picture, and they never have to agree with the real cuts.

**So the test is not agreement with the timeline.** A boundary is right when correcting across it makes the level more even, and wrong when it does not. Run `segment.py` on a slug to see that number for a run — it prints the spread before and after.

**A boundary survives on the larger of two measurements, and both are needed** (2026-08-14). One is the step *at the join* — the speech level `boundary_window_s` either side of it. The other is the step between the *whole segments* that meet there. Each catches what the other cannot: the join step finds a jump hidden by a clip's own fall across its length, and the whole-segment step finds two clips that genuinely differ but happen to meet at a matching moment.

**The whole-segment test on its own was the first build's one audible fault.** A cut is a discontinuity, and averaging a whole clip is the one operation guaranteed to hide one — a clip that opens loud and ends quiet averages out to its neighbour's level. On the reel that discarded the cut at `44.58s` (whole-segment step `0.99 dB` against a threshold of `1.0`; actual step at the join `5.51 dB`), which then dragged down the boundary next to it, and 22.7 seconds spanning three clips became one segment with one straight line fitted across all of it. The report was *"the clip at 00:46 is a lot louder than the clip before."*

**Loudness decides, always; the picture only points.** Scene scores nominate positions worth measuring and get no vote. That is what keeps this from being a content decision: the picture is asked *where to look*, never what is in the video.

### Never process its own output

The stage overwrites the transcript's `"video"` field, which means the field it would naturally read from is the field it destroys. So it takes the source from `01-video.md` — the file `read_video.py` writes and the person may hand-edit, which is the reason it exists — and never from the field it writes itself.

**If it is handed its own output anyway, the run stops.** It does not skip the step and carry on. Recognised by location: a source path sitting inside `paths.yaml`'s `audio_output` is this stage's own work. No marker, no filename convention, nothing to keep in sync.

### The CapCut project is not touched in this build

Not a standing refusal — a scoped one, with its reason. Three of the four operations here cannot be expressed as a CapCut clip setting at all: the high-pass removes rumble below 80 Hz, the within-clip correction needs a level that changes as the clip runs, and the ceiling must not be enforced by turning clips down. Only the between-clip offset is a per-clip volume, and writing it back would mean re-exporting a file the transcript no longer describes. **Reopens on its own evidence** if a later build needs the project.

---

## An instruction addresses the run, not one clip

*"If I say that I want the audio to be adjusted, then the program should do as I say."* The way to say it is an override in `memory/preferences.md` under `## Audio`, in that file's mechanical form — a backticked dotted key, `=`, a value.

**Whole-run, because the segments are the tool's own** and may differ between runs, so *"the third clip"* names nothing stable. The counter-case is on record: one clip on an earlier video was hand-lifted nearly 30 dB, rescuing a recording that came out far too quiet, and no run-wide setting does that. It has happened once across three videos. If it recurs, that is the moment to add a per-clip override — not before.

**An override naming a key that does not exist is reported, not obeyed and not ignored.** `preferences.md` warns that anything non-mechanical is *"prose for you, not for the script"*, so a mistyped key would otherwise do nothing silently. The run says which keys it did not recognise and carries on.

---

## What it flags

Deliberately dumb — no flag has a threshold of its own to tune.

| Printed | When | Why it is worth seeing |
|---|---|---|
| `kept N of M nominated` | every run | your eye catches "2 of 14" without the tool needing a rule for it. Loudness never adds boundaries, so kept can never exceed nominated |
| the running tally, and whether the loudness check has ever fired | every run | the one flag that outlives the run. A veto that has rejected nothing in ten videos is dead weight, and this is what makes that visible |
| the spread of the segment averages **and** the steadiness second by second | every run | both, labelled. The first improves by construction — it is computed from the very averages the correction is derived from, and it read `7.23 dB -> 1.81` on the run whose loud clip you heard. The second moves only when the video does |
| a segment merged for having too little speech | it happens | the decision printed rather than made silently |
| a correction that hit `max_correction_db` | it happens | the cap fires precisely when something upstream was probably wrong |
| the limiter working hard | it happens | it means the levelling pushed something too hot |
| an audio rule matching no config key | it happens | the failure this stage must not have is the silent one |

---

## Three self-checks, all of which stop the run

- **Same number of samples out as in.** Written for the re-encode risk; it catches a deletion just as well, whatever caused it.
- **The audio still starts with the picture** after the mux.
- **Same sample rate and channel count.**

The export is AAC, 44.1 kHz, two channels — and the two channels are bit-identical, so it is a mono recording in a stereo container. One channel is processed and copied to both; treating them independently risks them drifting apart and smearing the voice across the stereo image for no gain. A stage that "helpfully" wrote mono, or resampled to 48 kHz, would hand CapCut something different from what it exported.

---

## What this stage assumes about its input

**The export is voice-only.** *"Music comes after."* Both the speech measurement and the high-pass are built on it: a music bed would be measured as speech, and real content would go under the filter. The stage does not check for this — it is a rule about the person's own pipeline, recorded here so a later build does not quietly break it.

---

## Running it on its own

```
python3 stages/01b_calibrate/scripts/segment.py <slug>       what it would do, writes nothing
python3 stages/01b_calibrate/scripts/measure.py <slug>       the levels, nothing else
python3 stages/01b_calibrate/scripts/calibrate_audio.py <slug>
```

Re-running overwrites the previous output from the same source, so it is safe to run repeatedly. That is what makes setting the two correction amounts by ear practical — change a value, run, listen.

**`caption.py --redo` does not re-run this stage**, and that is why `REDO_FROM` sits below it. Correcting a word's spelling never changes the audio, so re-running calibration there would produce an identical file at the cost of the slowest step in the chain.
