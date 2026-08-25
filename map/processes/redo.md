---
name: redo
type: process
universe: live
status: verified
verified: 2026-08-26
consumes: [transcript, run-folder]
produces: [caption-cards, remotion-props]
---

# Redo

**Input →** a run slug whose `01-transcript.json` you corrected by hand. **Movement →** steps 4–6 only. **Output →** rebuilt cards, `.srt`, and video.

```
python3 caption.py --redo 2026-07-29-pricing-your-work-as-a-consultant
```

## Steps

1. `caption.py:127-129` — refuses any other argument. It reuses that run's video and topic, so passing them again could only contradict it.
2. `caption.py:132` — requires `01-transcript.json`, naming `transcribe.py` if absent.
3. `caption.py:135` — reads the topic back from `01-topic.md`.
4. `caption.py:136` — slices the step list from `REDO_FROM`, so **no step below index 3 runs**: no re-read of the video, no re-transcription, no re-levelling.

## Why it skips what it skips

**Re-transcribing would overwrite the correction you just typed with the same wrong word** — the one thing a rebuild must never do.

**Re-levelling would produce an identical file at the cost of the slowest step**, since a spelling fix never changes the audio. The audio stage refuses its own output as a backstop, but a safety rule that trips during ordinary work is one that gets switched off — so the boundary keeps it from ever firing in normal use (`caption.py:58-65`).

The boundary is a slice index derived from the step list, not a second copy of it. See [[step-list]].

## The full fix-a-word loop

1. Fix the word in `output/runs/[slug]/01-transcript.json`
2. `python3 caption.py --redo [slug]`
3. `python3 stages/04_learn/scripts/learn_words.py [slug]` → [[learn]] — **this is the step that makes it stick**

Step 3 is separate on purpose and is easy to skip; without it the same word comes back wrong next time.

## If you change this

**Hits**
- **Any step inserted at position 3 or below** becomes the first thing `--redo` runs. Check the transcript-write boundary.
- **Deleting [[levelled-audio]] before a redo** is fine — the render falls back to the original and prints why (`render_captions.py:56-72`).

**Does not hit**
- **`01-transcript-raw.json`.** Never touched, by anything, ever — which is what keeps the correction visible to [[learn]].
- **The tally or the lexicon.** `--redo` does not run stage 04.

## See

`caption.py:126-138` · root `CLAUDE.md`, "When a word comes out wrong"
