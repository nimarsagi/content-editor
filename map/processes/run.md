---
name: run
type: process
universe: live
status: verified
verified: 2026-08-26
consumes: [video-record, edit-defaults, lexicon, preferences, paths]
produces: [run-folder, transcript, levelled-audio, caption-cards, remotion-props]
---

# Run

**Input →** a finished CapCut export plus a one-line topic. **Movement →** six scripts in order. **Output →** one 1080×1920 file with captions burned on, in `render_output`.

```
python3 caption.py --topic "…"          the one video in input/
python3 caption.py 0728.mov --topic "…" that name, inside input/
python3 caption.py ~/Desktop/x.mp4 --topic "…"
```

## Steps

0. `caption.py:143` — **find the video**: an existing path, then a name in `input/`, then the only video in `input/`. Two videos and it refuses and lists them (`caption.py:104-106`) — guessing costs a full render before anyone notices.
1. `caption.py:149-151` — slug from date + topic; create the [[run-folder]]; write `01-topic.md`.
2. `read_video.py` — probe once, write [[video-record]].
3. `transcribe.py` — the topic gate runs **before the model loads** (`transcribe.py:62-73`), because transcription is the slow step. Then faster-whisper `medium`/`int8`, local, word timestamps required → [[transcript]] plus the write-once raw copy.
4. `calibrate_audio.py` → [[calibrate]], producing [[levelled-audio]] and repointing the transcript's `"video"` field.
5. `chunk_captions.py`, `write_srt.py` → [[caption-cards]].
6. `render_captions.py` → [[remotion-props]], then Remotion.

The run stops at the first non-zero exit and says which script (`caption.py:164-165`).

## What the run does not do

It stops to ask nothing (`identity.md`, "How it decides"). It proposes no cuts, removes no dead air, and decides nothing about content — `governance.md` rule 1. **Nothing calls a model** except transcription, which is local; `run_fixture_checks.py:318` asserts it.

## If you change this

**Hits**
- **The order cannot move.** Transcription happens on the finished file, once. Word timings taken from raw clips describe footage a later cut removes, and the error grows through the video — the failure mode of a previous attempt at this.
- **`--topic` is required** on a first run and seeds the transcription alongside [[lexicon]]. It is not decoration.
- **Changing the step list** → [[step-list]], and check which side of `REDO_FROM` a new step falls on.

**Does not hit**
- **`04_learn`.** Not part of a run; nothing waits for it.
- **CapCut.** The cutting happened before the file arrived and is never touched.

## See

`caption.py` · `CONTEXT.md` · root `CLAUDE.md`, "Running it"
