---
name: video-record
type: object
cluster: artifacts
universe: live
status: verified
verified: 2026-08-26
---

# Video record

`01-video.md` — where the **original export** lives, how long it is, and its frame rate. A markdown file parsed back by `read_record()` (`stages/01_ingest/scripts/read_video.py:34-52`).

## Why this shape

**It is the one file that survives a clear-out.** `01-transcript.json`'s `"video"` field gets repointed at the levelled copy, and `output/audio/` is deletable — so after one run there is no other record of where the original is. Both `calibrate_audio.py` and the renderer's fallback path depend on that.

Markdown rather than JSON because it is an edit surface: correct a value by hand and everything downstream uses the correction, since nothing probes the file a second time (`read_video.py:7-11`). One probe, one record, no chance of disagreement.

The frame rate is kept to six decimals (`read_video.py:79`). Rounding 29.97 to 30 drifts a frame every 33 seconds — four frames late by the end of a two-minute take.

## Shape

Three fields, matched by `_FIELD` (`read_video.py:31`) as `- **Name** — value`:

- **Path** — absolute, backticked (`read_video.py:77`)
- **Duration** — seconds, 3 dp
- **Frame rate** — fps, 6 dp

`read_record()` exits if any of the three is missing (`read_video.py:44-46`).

## Connected to

- **owned by** — [[run-folder]]
- **read by** — `transcribe.py:92`, `calibrate_audio.py:90`, `measure.py:239`, and `render_captions.py:63-64` on the fallback path only
- **looks like but is not** — [[transcript]]'s `"video"` field, which after calibration points at [[levelled-audio]], not at the original. The two must never be swapped: `calibrate_audio.py` reads *this* file precisely because it overwrites the other (`calibrate_audio.py:12-17`).

## If you change this

**Hits**
- **Changing the field format** breaks `_FIELD` and every caller above at once. The regex accepts `—` or `:` as separator and strips backticks; nothing else.
- **Editing the duration or fps by hand** flows into the caption timings (via the transcript) and the render length (`render_captions.py:48-51`) with no re-probe anywhere.
- **Deleting the file** makes every downstream stage exit through `lib.require` naming `read_video.py`.

**Does not hit**
- The already-written transcript. Correcting `01-video.md` after transcription does not retime existing words — re-run from `transcribe.py` (`stages/01_ingest/CONTEXT.md`, "Order").
- The audio stage's refusal check, which is by *location* under `audio_output`, not by anything written here (`calibrate_audio.py:62-76`).

## Surfaces

Written once by `read_video.py`. Read by three stages. Hand-edited by the person — that is its reason to exist.

## See

`stages/01_ingest/scripts/read_video.py:34-88` · `stages/01_ingest/CONTEXT.md`
