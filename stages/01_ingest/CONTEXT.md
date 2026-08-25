# 01_ingest — stage contract

**Takes** one finished video — your CapCut export, captions not burned in — plus a one-line topic.
**Gives back** a word-level transcript of it, twice: one for you to edit, one nobody ever touches.

---

## Inputs

| Input | Level | Notes |
|---|---|---|
| the finished export | **L4 — this run** | already cut. Nothing here removes anything. |
| the take's topic | **L4 — this run** | **required.** The run does not proceed without it. |
| `_config/lexicon.txt` | L3 — stable | passed to transcription as a bias prompt |

## Outputs

| File | Written by | What it is |
|---|---|---|
| `01-topic.md` | you, via `caption.py` | the topic, as you stated it |
| `01-video.md` | `read_video.py` | the path, duration and frame rate — **edit surface** |
| `01-transcript.json` | `transcribe.py` | word-level timings — **edit surface, this is where you fix a wrong word** |
| `01-transcript-raw.json` | `transcribe.py` | the same thing, untouched forever — **never edit it** |

## Order — read the video first, then transcribe

`read_video.py` runs first and writes down the duration and frame rate. `transcribe.py` reads them back out of `01-video.md` rather than probing again, so the two can never disagree — and so a hand-edit to that file actually takes effect.

---

## Three rules this stage exists to hold

### Word-level timestamps are non-negotiable

They are what makes splitting captions on breath and clause boundaries possible at all. A build that quietly downgrades to sentence-level timing looks fine here and destroys the caption stage. `transcribe.py` aborts by name if the model comes back without them.

### The topic is required, and the stage aborts without it

It goes to the transcriber as context, alongside the lexicon, and the model mangles fewer of the words that carry the meaning for having it. It is also how you will recognise this run in six months.

The check runs **before** the model loads, because transcription is the slow step and failing after it wastes minutes for something testable in a millisecond.

### The raw transcript is written once and never again

`governance.md` rule 3, and this stage is where it is enforced: `transcribe.py` refuses to replace `01-transcript-raw.json` if it already exists, and says so.

---

## Why the frame rate is kept to six decimal places

Phones and editors both produce 29.97 fps, not 30. Rounding drifts by one frame every thirty-three seconds — four frames late by the end of a two-minute take, which is where caption sync visibly goes wrong. `probe_frame_rate` divides the fraction ffprobe reports and never rounds it.
