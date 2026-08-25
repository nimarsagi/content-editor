# audio-measurements.md — what the audio actually is

**Provenance, not config. No script opens this file** — the fixture checks
assert that, the same as for every other file in `source-specs/`. The numbers
here were copied by hand into `_config/edit-defaults.yaml` under `rules: audio:`,
each with its reason. This is where you come to find out whether a value is worth
keeping.

Measured 2026-07-31 / 2026-08-01 with `tools/measure_audio.py` and `ffmpeg`, on
real exports from this workspace. Two videos, and the second one is what makes
most of the conclusions safe to draw — a single take could not tell a property of
the person's speech apart from a property of one recording.

---

## The two videos

| | `0731.mov` — the reel | the earlier video |
|---|---|---|
| length | 55.6 s, 10 clips, 216 words | 81.5 s, 17 clips, 293 words |
| run | `0731-ai-resistance` | `2026-07-30-why-telling-ai-to-use-fewer-tokens-does-` |
| speech level | **-26.0 dBFS** (median voiced frame) | — |
| background | **-54.0 dBFS** | **-42.4 dBFS** |
| separation | 28.0 dB | 17.6 dB |
| peak | **-0.1 dBFS** | **-3.0 dBFS** |
| silence between words | 11% | 10% |
| median gap | 0.24 s | 0.15 s |
| spread across clips | **7.0 dB** | — |

A third recording, measured alongside: peak `-0.2 dBFS`, background
`-56.2 dBFS`, background energy 92% below 1 kHz — a steady low rumble, not hiss.

### Two conclusions that needed both videos

**The speech is dense, and that is how the person speaks.** 10-11% silence on
both. Not a property of one take. Any future design that assumes usable silence
between words should be checked against this first — it is what killed per-clip
room tone sampling, and it is why levels are measured on speech spans rather than
on whole regions.

**No absolute threshold survives a second video.** Background moved 12 dB and
separation nearly halved. A setting tuned on one is wrong on the other.

> **Scope of that rule, recorded so it is not read as unmet.** It is about
> *detecting* something against background noise, which is breath work and is not
> in this build. The values this build holds are a different kind — a peak
> ceiling, correction percentages, minimum lengths, a filter frequency — and none
> is measured against background level. The one value it arguably *does* catch is
> `min_step_db`; see the open question at the end.

---

## Why levelling is needed at all

**The hand-levelling being replaced is exhaustive, and it is not working.**

The reel measures a **7.0 dB spread across clips** — *after* two of its ten clips
were already hand-set in CapCut (`1.149` and `0.866`).

The earlier video has **all 17 clips hand-set, every one to a different value**:

```
0.327  0.330  0.359  0.369  0.385  0.411  0.442  0.458  0.474
0.490  0.491  0.492  0.504  0.554  0.555  0.611        and one at 10.0
```

Not one clip left at `1.000`. A 5.4 dB span of deliberate adjustment, plus a
single clip pulled up by nearly **30 dB** against the quietest — someone rescuing
a recording that came out far too quiet.

That last one is also the counter-case for whole-run instructions: no run-wide
setting rescues one clip like that, and `max_correction_db` may well block the
tool from doing it either. It has happened once across three videos. If it
recurs on a real run, that is the moment to add a per-clip override — not before.

**The ceiling is a separate matter and it is not universal.** Peaks of `-0.1`,
`-0.2` and `-3.0 dBFS`. Two of three sitting at the ceiling. So the limiter is a
safety net that often does nothing, while levelling runs every time. They are not
two halves of one operation and are not built as one.

---

## Within-clip drift is the larger problem

Measured on the reel: **nine of ten clips are quieter at the end than the start.**

```
mean fall     5.4 dB
worst         9.6 dB
one clip      +1.6 dB   ← drifts UP, which is why the correction is symmetric
```

Against `1.0-2.9 dB` *between* clips. Roughly two and a half times larger.

**Why the correction cannot pump.** It moves across seconds, not syllables, and
the gain updates only at word boundaries. Across a 6-second clip of ~20 words,
correcting 5.4 dB puts each word about **0.27 dB** from its neighbour — below
what anyone hears as a step, and no gain moves while a word is playing.

**Why gain may only change at a word boundary.** A level change mid-word is
audible; the same change in the gap before it is not. The gaps are short but
ample: median 0.24 s and 0.15 s, against a ramp measured in tens of milliseconds.

---

## Segmentation: the picture nominates, loudness decides

**Why the picture is consulted at all — the arithmetic.**

```
step in level across a real cut        1.0 - 2.9 dB   (median 2.2)
frame-to-frame spread inside a clip    6.9 dB sd
```

The thing being looked for is a third the size of the noise it hides in. Hunting
unknown change points in that series means testing hundreds of positions against
a signal that small — it will invent boundaries. **But given a position to test,
the same measurement is easy**, because averaging a whole clip's voiced frames
collapses the uncertainty:

```
uncertainty on a clip's level     +/- 0.35 to 0.61 dB   (worst = shortest clip)
median real step                  2.2 dB  =  5.0x the uncertainty
smallest real step                1.0 dB  =  1.6x the uncertainty
```

**Scene scores against CapCut's real cuts, both videos:**

```
                        0731 reel        earlier video
real cuts                 9                17
nominated by picture      9  (all)         16
missed                    0                 1   ← 1.700s, scene score 0.005
extra nominations         0                 4   ← from an overlay track
lowest real cut score     0.187             0.005
highest false score       0.052             0.336
```

- **The missed one is a jump cut** — two clips shot in the same place at the same
  framing, so nothing visibly changes. It scores `0.005`, indistinguishable from
  camera shake. It only matters if the level actually differs there; if it does
  not, missing it costs nothing.
- **The false ones came from a second video track** — b-roll over the top. Two
  score `0.336`, higher than most real cuts, **so no threshold separates them.**
  They are discarded by the loudness test instead: an overlay does not change the
  audio, so no level step is found and no boundary is kept.

### What `scene_threshold` actually produces — measured 2026-08-03

The design argued for a very low threshold: extra nominations are nearly free —
a spurious boundary splits one recording into two segments that measure the same
and get the same correction — while a missed one is unrecoverable. **That holds
for a handful of extras. It does not hold for what a low threshold really
produces here.** Both videos, run through the nomination step:

```
                    0731 reel (9 cuts)      earlier video (17 cuts)
scene > 0.004       393 nominations         673 nominations
                    median span 0.07s       median span 0.03s
                    100% of spans <1s        99% of spans <1s
scene > 0.01         57                     173
scene > 0.03         14                      28
scene > 0.05         10                      20
                    median span 5.67s       median span 4.10s
                      0% of spans <1s        16% of spans <1s
scene > 0.10          9                      18
```

At `0.004` the picture nominates **40x more positions than there are cuts**,
spaced 30-70 ms apart. The `+/- 0.35 to 0.61 dB` uncertainty above holds
*because* a whole clip's voiced frames are averaged; over a 0.03 s span there is
nothing to average, the margin collapses, and testing 673 positions against a
step near the noise floor is the "it will invent boundaries" regime exactly.

**Settled at 0.05**, where nominations land near the real cut count and every
span is long enough to measure. What that gives up, knowingly: the `0.005` jump
cut. No threshold catches it without catching everything, because there is
nothing there to see — and it only costs anything if the level genuinely differs
across it.

**And why agreement with CapCut is not the test.** The person owns the edit; the
tool's boundaries are only the places its gain may change. *"Whatever you cut is
based purely on averaging out the audio. Not content."* So a boundary is right
when correcting across it makes the level more even, and wrong when it does not.
The 9-of-9 and 16-of-17 counts are a sanity read underneath that, not the gate.

### Where the step is measured — measured 2026-08-14, after the first real listen

The report on the first shipped run: *"the clip at 00:46 is a lot louder than the
clip before."* The cause was not the threshold. It was **what the threshold was
applied to.**

The test compared the average level of the whole segment before a position
against the whole segment after it. **A cut is a discontinuity, and averaging a
whole clip is the one operation guaranteed to hide one.** The clip starting at
`44.58s` opens at `-20.13 dB` and ends near `-29`; its average of `-25.06` sits
within 1 dB of its neighbour's `-24.07`. The join read as flat because the clip's
own fall cancelled its loud opening.

**Every nominated boundary on both videos, measured both ways.** `local` is the
speech level `2 s` either side of the join; `kept` is what the whole-segment test
alone decided.

```
0731 reel                              2026-07-30 video
 boundary   whole-seg   local   kept    boundary   whole-seg   local   kept
   2.20s      1.10      1.38    yes       2.99s      0.23      5.99    NO
  10.06s      2.21      6.01    yes      13.66s      0.49      8.64    NO
  15.56s      2.07      0.51    yes      19.44s      0.08      2.30    NO
  19.23s      3.07      2.33    yes      22.45s      1.74      2.67    yes
  23.22s      2.51     10.92    yes      30.46s      0.89      4.21    NO
  28.90s      2.75      6.07    yes      39.19s      3.94      0.86    yes
  38.78s      1.04      5.97    NO       44.64s      0.72      1.52    NO
  44.58s      0.99      5.51    NO       48.51s      1.54      0.13    yes
  51.56s      1.92      6.05    yes      52.09s      2.01      7.64    yes
                                         56.34s      3.17      3.14    yes
                                         60.42s      2.67      1.41    yes
                                         66.84s      0.17      3.18    NO
                                         72.85s      4.34      6.39    yes
                                         77.84s      6.52      6.54    yes
```

**Six of fourteen boundaries on the second video were being discarded while
carrying joins of 1.5 to 8.6 dB.** The disagreement runs both ways — `15.56s` and
`48.51s` were *kept* on a whole-segment step while their joins are flat to within
0.5 dB — which is what makes this a wrong measurement rather than a threshold set
too high. **Hence `max(local, whole_segment)`: neither term can be dropped.**

`boundary_window_s: 2.0` is **borrowed, not tuned.** It is `min_drift_fit_s`,
this workspace's existing statement of the least speech a level trend can be read
from, and it separates the joins from the non-joins cleanly across all fourteen
positions above. One value, taken from an existing one, checked against fourteen
joins.

**What the merge cost, on the clip that was reported:**

```
44.58-51.56s fitted on its own     slope -1.149 dB/s  =  -8.02 dB across the clip
inside the merged 28.90-51.56s     slope -0.063 dB/s  =  -1.43 dB across 22.7s
```

The drift correction was working correctly on a segment that was wrong. An 8 dB
fall was presented to it as a 1.4 dB one.

### The reported number was the wrong number — 2026-08-14

The first build's headline, *"spread 7.23 dB -> 1.81 dB"*, is the spread of the
**segment averages**. That is the quantity the offsets are computed from, so it
improves by construction — it was true, and it was blind to exactly what was
heard. Measured instead as the level over **one-second windows** across the whole
file, which is roughly what the ear follows:

```
                              0731 reel            2026-07-30 video
                            sd    p10-p90        sd    p10-p90
uncorrected               3.35     8.81        3.50     7.78
as first built            2.78     7.10        3.03     6.28
with the step at the join 2.63     7.19        2.67     5.15
  and within_clip = 0.75  2.50     6.31        2.61     4.81
```

Both figures are now printed, labelled, so they cannot be read for each other
again. The window is `diagnostics.heard_window_s` — a reporting choice, acted on
by nothing.

### The within-clip correction follows the level — measured 2026-08-14, second listen

After the boundary fix: *"the sound is still inconsistent across the video. Some
parts are significantly louder than others."* Measured on the delivered file, the
reel had **10 seconds sitting more than 3 dB from its own average and 4 more than
5 dB**, worst `7.04 dB`. Those seconds sit *inside* segments that were corrected —
only one segment per video is skipped for having too little speech.

**A straight line can only remove a tilt, and the level inside a clip humps.**

**Per-word levels are too noisy to smooth, which is the finding that decided the
shape of the fix.** On the reel, **26 of 216 words carry fewer than five voiced
frames**, and within two seconds the per-word medians run from `-11.43 dB` on
*"this"* to `-51.71 dB` on *"is"* — short function words measured from almost
nothing, not a voice moving 40 dB. So smoothing the word levels barely helped
(sd `2.35 -> 2.25` at a 2 s window), while reading the level from a **window of
audio**, which weights each word by how long it actually sounds, worked:

```
                        seconds >3 dB off   >5 dB   worst   word-to-word p95
uncorrected                    22             8      7.94        —
straight line                  11             4      6.26      2.54 dB
window of audio, 3.0s          10             2      6.14      2.07
                     2.0s       6             0      4.41      2.77
                     1.5s       2             0      4.15      3.35
                     1.0s       4             0      3.54      5.58
```

`drift_window_s: 1.5`. **The trade is word-to-word movement**, which is what
eventually sounds worked-on: `3.35 dB` at the 95th percentile against the line's
`2.54`. Still measured over more than a second, still changed only in the gaps
between words, still ramped. Raise it if a finished video sounds processed.

**Verified on the written file, not just predicted:** `10 -> 3` seconds more than
3 dB out, `4 -> 0` more than 5 dB, worst `7.04 -> 4.00 dB`, and the limiter did
`0.00%` of the file at both settings.

**The largest thing left is the opening 2 seconds** — `1.73s` of speech under
`min_drift_fit_s: 2.0`, so it is never corrected, at `+3.6 dB`.

---

## The shape of the file must not change

Measured on `0731.mov`: **AAC, 44.1 kHz, two channels** — and the two channels
are **bit-identical**. Maximum difference between left and right across
2,452,416 frames is exactly zero. It is a mono recording carried in a stereo
container.

Two consequences:

- **Process one channel and copy it to both.** Treating them independently risks
  them drifting apart, which smears the voice across the stereo image for no gain.
- **Do not "helpfully" convert.** A tool that writes mono, or resamples to 48
  kHz, changes the file's shape even though it sounds the same — and CapCut
  receives something different from what it exported.

Neither was raised in the interview. Both were found by measuring.

---

## The high-pass

Nothing in speech lives below 80 Hz. The second recording's background sits 59%
below 300 Hz; the third's, 92% below 1 kHz. Low rumble, not hiss. Removing it
costs nothing and is the cheapest single improvement available — which is why it
runs always, and runs *first*, so no level is ever measured with rumble in it.

---

## Open, and carried here so it is not lost

**`min_step_db` may not deserve to be a fixed number.** A nomination threshold as
low as `0.004` produces many nominations, and the span between two adjacent ones
can be far shorter than a real clip — `2.13s` and `1.30s` were the shortest
measured. The `+/- 0.35 to 0.61 dB` uncertainty holds *because* a whole clip's
voiced frames are averaged; over a short span it is larger, and `1.0 dB` stops
being 1.6x the noise. Testing many short spans against a step near the noise
floor is exactly the regime that invents boundaries.

What settles it is one measurement, not an argument: **run the nomination step
over both videos and count what `0.004` actually produces.** That number decides
whether this is a real problem or a non-issue.

**The earlier video may have music baked into it.** Its CapCut project contains
an audio track at volume `0.243`, and its export's quiet stretches sit about
10 dB louder than the reel's, with the energy concentrated at 300-1000 Hz — where
the reel's background is not. Consistent with music; also consistent with a
noisier room. The measurement cannot tell them apart.

**Why it matters:** that video is one of the two the "no absolute threshold
survives" conclusion rests on, and its background level is the headline number in
it. The conclusion holds either way — thresholds must still be derived per run —
but if it is music, that video is not a clean sample of what this tool receives,
and a second real voice-only export should replace it as evidence.

**One-minute check:** play a gap between words in that export and listen for
music. That settles it.
