# CONTEXT.md — what runs when

One pass, start to finish, no stopping in the middle.

```
   caption.py <video> --topic "..."

   01_ingest        01b_calibrate    02_assemble        03_render
   read the video   even out the     caption cards      burn them on
   transcribe       audio levels     the .srt sidecar   -> the file you post
```

Then, only if a word came out wrong:

```
   you fix it in 01-transcript.json      04_learn
   re-run 02 and 03 to rebuild           tally it, propose the lexicon entry
```

**04_learn is not part of a run.** It is what you do afterwards, when you noticed something. It never runs on its own and nothing waits for it.

---

## Stage by stage

| Stage | Takes | Gives back |
|---|---|---|
| **01_ingest** | the finished export + a one-line topic | its duration and frame rate, then a word-level transcript — twice, one yours to edit and one untouched |
| **01b_calibrate** | the export + the word timings | a copy of the export whose voice holds a steady level, clip to clip and inside each clip, without reaching the top of the meter |
| **02_assemble** | that transcript | caption cards inside the duration and width rules, plus an `.srt` |
| **03_render** | the cards + the video | one 1080×1920 file with the captions burned on |
| **04_learn** | your edits to the transcript | a tally across runs, and a lexicon proposal once a word has been wrong twice |

---

## Why the order cannot move

**Transcription happens on the finished video, and cutting happens before that, in CapCut.**

This is correctness, not preference. Word timings taken from raw clips describe footage that a later cut removes, so every caption after the first cut lands late, and the error grows through the video. Because this pipeline only ever sees a file that is already cut, the words and the pictures cannot disagree.

The practical consequence: **nothing here removes anything.** Filler sounds, pauses, a sentence you started twice — if it survived your edit in CapCut, it gets captioned. A component that quietly dropped a word would be rewriting what you said.

One rule follows from that and is easy to miss. A caption is held on screen until the next one starts, so it never flickers off in the beat between two phrases — **but only up to the duration ceiling.** Past that the video is genuinely silent, and a pause you left in for emphasis must not have the previous sentence sitting on top of it.

---

## Shared resources — what every stage may read

| File | What it is | Level |
|---|---|---|
| `_config/edit-defaults.yaml` | thresholds, typography, the anchor — **rules and diagnostics kept separate** | stable (L3) |
| `_config/lexicon.txt` | known terms seeding transcription | stable (L3) |
| `_config/paths.yaml` | where renders and levelled audio are written | stable (L3) |
| `memory/preferences.md` | pacing and audio overrides, each with its reason | stable (L3) |
| `01-transcript.json` word spans | **read by `01b_calibrate` too** — levels are measured on speech only, and this is what says where speech is | per run (L4) |
| `memory/caption-fixes.md` | the across-runs tally of corrected words | stable (L3) |
| `reference/terminology.md` | what the words mean here | stable (L3) |
| `reference/source-specs/` | **provenance only — no script opens these** | stable (L3) |

---

## Where the cost goes

**Nothing in this workspace calls a model.**

A run costs transcription — which is local, on your own machine, with no account and no subscription — and nothing else. Every decision is a local script reading an explicit threshold from `_config/edit-defaults.yaml`.

That was not always true; two model call sites went with the cut-proposal stage (`BUILD-NOTES.md`). **A new model call site is a decision to make deliberately, not something to slide in.** The fixture checks assert there are none.
