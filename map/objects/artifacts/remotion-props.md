---
name: remotion-props
type: object
cluster: artifacts
universe: live
status: verified
verified: 2026-08-26
---

# Remotion props

`03-remotion-props.json` — exactly what the renderer was handed. The only channel between the Python side and the React side.

## Why this shape

**The renderer decides nothing.** Every visual constant is read out of `_config/edit-defaults.yaml` here and passed across (`render_captions.py:210-233`); `remotion/src/types.ts:1-10` states the same rule from the other end. A caption style that drifts from the config is invisible in any single video — you only catch it by comparing two, months apart.

The file is written whether or not the render succeeds, so a failed render is exactly reproducible: `cd remotion && npx remotion studio src/index.ts` with these props (`render_captions.py:256-262`).

## Shape

Four keys, typed in `remotion/src/types.ts:47-52`:

- `videoSrc` — a *filename*, relative to `remotion/public/`, staged there by `stage()` (`render_captions.py:107-153`)
- `cards` — [[caption-cards]] verbatim, `lines[]` already wrapped
- `style` — 10 fields, all from config, except `lineHeightEm: 1.3` which is **hardcoded** at `render_captions.py:221` and also used in the geometry assertion at `:159`
- `meta` — canvas from config; `fps` and `durationInFrames` from [[transcript]], never re-probed (`render_captions.py:48-51`)

`durationInFrames` is ceiled (`render_captions.py:231`) so a final part-frame is not dropped.

## Connected to

- **owned by** — [[run-folder]]
- **consumes** — [[caption-cards]], [[transcript]], [[edit-defaults]] `typography:` + `geometry:`
- **read by** — `remotion/src/Root.tsx`, `remotion/src/CaptionedVideo.tsx`
- **looks like but is not** — the render output. This is the input; the `.mp4` goes to `render_output` — see [[paths]].

## If you change this

**Hits**
- **Adding a style field** means three edits in step: `render_captions.py:213-224`, `remotion/src/types.ts`, and the component that consumes it. A prop added on one side only fails at render time, minutes in.
- **The geometry assertion runs first** (`render_captions.py:156-175`) — a block at the configured anchor must clear `bottom_limit_px` and the size must clear `legibility_floor_px`, or nothing renders. That is deliberate: a safe-zone breach is invisible in a progress bar and visible once, on the phone, after the wait.
- **`lineHeightEm` is written twice** — the assertion at `:159` and the prop at `:221` both hardcode `1.3`. Change one and the assertion stops describing what renders.

**Does not hit**
- **The cards.** Re-rendering with different typography does not re-chunk; the line breaks were fixed in stage 02 against the *old* character budget. Change `caption_size_px` and you must re-run `chunk_captions.py`, not just the render (`render_captions.py:195-197` notes the split deliberately).
- **The font file.** `font-data.ts` is regenerated from the tracked `.ttf` every render (`render_captions.py:77-104`) and is not tracked.

## Surfaces

Written by `render_captions.py`. Read by Remotion via `--props`. Never hand-edited, but it is the artifact to look at when a render comes out wrong.

## See

`stages/03_render/scripts/render_captions.py:194-236` · `remotion/src/types.ts` · `stages/03_render/CONTEXT.md`
