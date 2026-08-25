# 03_render — stage contract

**Takes** the caption cards and the video.
**Gives back** one 1080×1920 file with the captions burned on — the thing you post.

---

## Inputs

| Input | Level | Notes |
|---|---|---|
| `02-caption-cards.json` | **L4 — this run** | the cards, already laid out into lines |
| `01-transcript.json` | **L4 — this run** | for the video path, duration and frame rate |
| `_config/edit-defaults.yaml` | L3 — stable | every style constant |
| `_config/paths.yaml` | L3 — stable | where the finished file is written |

## Outputs

| File | Written by |
|---|---|
| `03-remotion-props.json` | `render_captions.py` — exactly what Remotion was handed |
| the finished `.mp4` | Remotion, into `render_output` |

---

## The renderer decides nothing

Every constant — size, weight, colour, the anchor, the line cap, the shadow — is read out of `_config/edit-defaults.yaml` here and passed to Remotion as props. **The React side has no defaults of its own worth the name.** Two reasons that matters:

- **The line cap and the font are a matched pair.** `chars_per_line_derived` was computed from Inter SemiBold's character advance. If the renderer picked its own font, the wrapping done in stage 02 would no longer describe the pixels, and the longest lines — the ones most likely to be cropped — would be the ones that overflowed.
- A caption style that drifts from the config is invisible in any single video. You only catch it by putting two side by side, months apart.

---

## Why the numbers are read, not re-probed

The duration and frame rate come from `01-transcript.json`, not from a fresh look at the file. Those are the numbers the caption timings were built against, so probing again could only introduce a disagreement — and a frame rate that disagrees with the one the cards were timed to is exactly how captions drift out of sync.

## The geometry is asserted before anything renders

A render takes minutes, and a breach of the safe zone is not visible in a progress bar — it is visible once, on the phone, after the wait. So the arithmetic runs first: a full two-line block at the configured anchor must clear the bottom margin, and the font must be above the legibility floor. Either fails and nothing renders.

**The safe zone is a conservative envelope from third-party guides, not a published platform spec.** Only an export checked on the phone, in both apps, closes that question. No assertion here can.
