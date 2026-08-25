# CLAUDE.md — Content Editor Entry Contract

**You are operating the content editor.** This file is the entry contract — read it before responding to anything else.

---

## What this workspace is

**One finished video in, one captioned video out.**

You film in bursts, cut it together in CapCut, and export without captions. This pipeline transcribes that export, groups the words into readable caption cards, and burns them on with Remotion. It replaces a paywalled subtitle generator, and it runs locally.

```
your CapCut export  ->  transcribe  ->  level the audio  ->  caption cards
                            |                                     |
                       you fix a wrong word                    burn on
                            |                                     |
                       it remembers, and stops               ->  posted
                       getting it wrong
```

**The cutting is not part of this.** It happens by hand in CapCut, before anything reaches here. The tool captions what you hand it and never decides what goes in the video.

---

## The trigger

**"Add subtitles to this video", "caption this", "burn the captions on", or a video handed over with no instruction — all mean: run the pipeline.** Do not build anything, and do not write your own transcription or captioning code. It exists, it is tested, and it is one command.

What you need before running, and how to get it without asking twice:

| You need | Where it comes from |
|---|---|
| the video | a path they gave you; a name in `input/`; or the only video in `input/` |
| `--topic`, one line on what the take is about | **ask them**, or propose one from the filename and have them confirm. It seeds the transcription and measurably reduces mangled terms |

Then run the command under **Running it** below and report where the file landed. A render of a two-minute video takes several minutes — say so before starting rather than going quiet.

**If a word came out wrong, do not re-transcribe.** See *When a word comes out wrong*; re-transcribing overwrites the correction with the same mistake.

---

## The one thing every component has to know

**The video arriving here is already cut, and every word timing belongs to it.**

That is what makes the captions line up. Transcribing raw clips and cutting afterwards would leave every timing pointing at footage that no longer exists, and each caption would drift further out of sync as the video went on — which is exactly how a previous attempt at this failed. Nothing in this workspace may reorder that: transcription happens on the finished file, once.

You film in tiny clips because you forget your text past a few seconds, and a sentence routinely starts in one clip and finishes in the next. **That matters in CapCut and nowhere else.** By the time the export reaches here the joins are baked in and invisible, so no component knows or needs to know that the take was filmed in pieces.

---

## Read order — and when it applies

**To run the pipeline, run it.** Everything a run needs is on this page: the trigger, the command, and the fix-a-word loop. A run consults none of the files below — no script opens them and no decision in a run turns on them. Reading them first buys nothing and costs a few thousand tokens before you have typed anything.

**Before changing anything** — a threshold, a script, a stage contract, this file — read in this order:

1. `identity.md` — what this is and what it refuses
2. `governance.md` — the four rules, including the approval gate on writes
3. `CONTEXT.md` — which stage runs when

Then the routing table below for the stage you are touching.

---

## Routing table

| Task | Stage | Read |
|---|---|---|
| Read the video, transcribe it | `01_ingest` | `stages/01_ingest/CONTEXT.md` |
| Anything about audio levels, loudness, peaks | `01b_calibrate` | `stages/01b_calibrate/CONTEXT.md`, `_config/edit-defaults.yaml` |
| Build caption cards, write the `.srt` | `02_assemble` | `stages/02_assemble/CONTEXT.md`, `_config/edit-defaults.yaml` |
| Burn the captions on | `03_render` | `stages/03_render/CONTEXT.md`, `_config/paths.yaml` |
| Turn a corrected word into a lexicon entry | `04_learn` | `stages/04_learn/CONTEXT.md` |
| Anything about a word's meaning here | — | `reference/terminology.md` |
| **What else a change would hit** | — | the map in `../video-pipeline-cartographer/` — a separate repo kept beside this one; catalog in its `examples.md`. If it isn't beside this checkout, ask for it rather than walking the tree |

---

## Folder map

```
content-editor/
├── CLAUDE.md · CONTEXT.md · identity.md · governance.md   ← the engine's contract
├── caption.py                 ← the entry point: one video in, captioned out
├── input/                     ← drop a video here. Contents untracked — it is your footage
├── pipeline_lib.py            ← shared plumbing. No thresholds, no paths.
├── stages/01_ingest · 01b_calibrate · 02_assemble · 03_render · 04_learn
├── memory/       preferences.md · caption-fixes.md
├── map/          superseded — the map of this repo lives in
│                 ../video-pipeline-cartographer/ (catalog in its examples.md)
├── reference/    terminology.md · source-specs/
├── _config/      edit-defaults.yaml · lexicon.txt · paths.yaml
├── remotion/     the caption renderer. Holds NO constants of its own;
│                 every value arrives as props from _config
├── tools/        sync.py · make_fixture.py · make_fixture_video.py ·
│                 run_fixture_checks.py · render_smoke_test.py ·
│                 measure_audio.py — NOT a dev tool: 01b_calibrate
│                 imports it at runtime
├── .claude/      the hook that runs sync.py after every edit
└── output/       everything the tool produces. Untracked, safe to clear.
    ├── runs/[YYYY-MM-DD-slug]/   ← one run's full trail
    └── audio/[slug]/             ← the levelled copy of your export
```

**Engine vs config.** Everything outside `_config/` is the reusable engine. `_config/` holds only what changes if someone else deployed this: their thresholds, their terms, their disk paths. **No threshold, font size, or filesystem path may appear in a script.**

---

## Running it

```
python3 caption.py --topic "pricing your work as a consultant"      the one video in input/
python3 caption.py 0728.mov --topic "..."                           that name, inside input/
python3 caption.py ~/Desktop/my-export.mp4 --topic "..."            any path
python3 caption.py --redo 2026-07-29-pricing-your-work-as-a-consultant
```

Drop a video in `input/` and the first form finds it. With two videos in there it refuses and lists them — guessing would cost a full render before anyone noticed.

The topic is required on a first run. It seeds the transcription — the model gets it as context and mangles fewer of the words that carry the meaning — and it names the run.

`--redo` takes only the run's name, because it reuses that run's video and topic. It is the whole fix-a-word loop in one command.

---

## The run folder

One run produces one folder, `output/runs/[YYYY-MM-DD-slug]/`, whose files carry the stage number that produced them so the trail reads in order:

| File | Written by | Editable by hand |
|---|---|---|
| `01-topic.md` | you, at invocation | — |
| `01-video.md` | `read_video.py` | yes |
| `01-transcript.json` | `transcribe.py` | **yes — this is where you fix a wrong word** |
| `01-transcript-raw.json` | `transcribe.py` | **never.** It is the only record of what the model actually heard |
| `02-caption-cards.json` | `chunk_captions.py` | yes |
| `02-captions.srt` | `write_srt.py` | yes |
| `03-remotion-props.json` | `render_captions.py` | — |
| `04-proposed-words.md` | `learn_words.py` | **approval gate** |

Every one of these except the raw transcript is a human edit surface: fix a word in `01-transcript.json` and run `caption.py --redo [slug]`.

---

## When a word comes out wrong

1. Fix it in `output/runs/[slug]/01-transcript.json`
2. `python3 caption.py --redo [slug]` — rebuilds the cards, the `.srt` and the video
3. `python3 stages/04_learn/scripts/learn_words.py [slug]` — **this is the step that makes it stick**

`--redo` deliberately does **not** transcribe again. Re-transcribing would overwrite the correction you just typed with the same wrong word, which is the one thing a rebuild must never do.

It compares your version against the untouched original and tallies what you changed. A word you have corrected in **two separate runs** gets proposed for `_config/lexicon.txt`, which biases the next transcription toward it. Nothing is added without your yes.

---

## After changing anything

```
python3 tools/sync.py
```

Checks the syntax and runs the fixture checks. **The hook in `.claude/` does this by itself** after every edit, when this folder is the session's project. The hook holds no logic of its own; it only calls `tools/sync.py`.
