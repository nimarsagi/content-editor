# Reel Edit Spec — @askcatgpt style
Source: 3 reels analysed frame-by-frame (Instagram, July 2026)
- **R1** `DbMhNTIi9cX` — "Why AI isn't actually improving your workflow" — 93.7s, 1080×1920 (sponsored)
- **R2** `DaYk-4IBot2` — "Stop trying to spot every AI video" — 76.8s
- **R3** `DbG_EO6yVig` — "Anthropic have agreed to answer your hard questions" — 63.6s

Numbers marked (m) are measured from frame-difference sampling at 0.1–0.2s resolution.
Numbers marked (e) are estimates and are the knobs most worth tuning.

---

## 1. Container
- 9:16, 1080×1920, single continuous vertical selfie/handheld A-roll per location.
- Target length **60–95s** (m: 63.6 / 76.8 / 93.7). This is long-form talking head, not a 15s hook reel.
- Camera is locked / near-locked per reel: background is identical across cuts, so all cuts read as jump cuts rather than angle changes.
- No outro card, no logo bug, no progress bar, no music-video style beat sync.

---

## 2. Subtitles (the main automation target)

### Cadence relative to speech
- Captions are **phrase-chunked, not word-by-word karaoke**. No per-word highlight, no colour change, no pop or scale effect. Each card appears and disappears as a whole block.
- **~1.0–1.5s per card** (m: 22 caption changes measured between 16.2s and 39.6s in R1 → mean 1.06s/card).
- **4–6 words per card** typical, hard ceiling around 10–11 words.
- Speech rate is fast (~180–210 wpm), so cards are wall-to-wall: there is essentially **no gap between cards** while she is talking. Card N ends the frame card N+1 begins.
- Cards break on **breath/clause boundaries**, not on line-fill. Examples of consecutive cards from R1: `In all of these` → `"what I learned at Cannes" recaps,` → `you may have noticed` → `that one thing that is`. From R2: `we should be trying to get good at spotting` → `AI video`. That 2-word orphan card is deliberate — the sentence is split where she pauses, even if the second half is tiny.
- Captions start on **frame 1** (R2's cover frame already has `Hot take, I do not think` burned in). No fade-in on the first card.

### Suggested automation rules
```
chunking:
  mode: phrase
  target_words: 4-6
  max_words: 11
  max_lines: 2        # R1; R2/R3 occasionally allow 3
  max_chars_per_line: ~26
  split_on: silence >= 120ms OR clause punctuation (, . ? —)
  allow_orphan_cards: true      # do not merge a 2-word tail into the previous card
timing:
  min_duration: 0.6s
  target_duration: 1.0-1.5s
  max_duration: 2.5s
  gap_between_cards: 0 frames
  lead_in: 0        # card appears on the first phoneme, no anticipation
  card_effects: none   # no pop, no karaoke highlight, no typewriter
```

### Look and position
- Centred horizontally, **fixed vertical anchor at roughly 65–72% of frame height** (R1 sits lower, ~72%; R2/R3 ~65%). The anchor never moves within a reel — pick one and keep it.
- White, geometric/humanist sans (Poppins / Avenir-Next / Century-Gothic family look), sentence case, soft dark drop shadow rather than a hard stroke. No background box, no pill.
- Two weight variants observed: R1 uses a heavier, fully opaque weight; R2 and R3 use a lighter, slightly translucent white. Treat this as a per-reel preset rather than mixing.
- Punctuation is preserved and casual: commas, question marks, and **double quotes for reported speech** (`"oh my god,` / `to human creativity?"` — the quote opens on one card and closes on a later card, which means the automation must not strip or auto-balance quotes per card).
- **Subtitles are always the topmost layer.** They render on top of every overlay, even when a b-roll card covers the whole middle of the frame (R1 @31s, R2 @6s).

---

## 3. Cutting

### A-roll
- Continuous take, pauses removed by **invisible jump cuts** on the same framing. Detected A-roll cut points in R1: 4.6s, 6.4s, 8.0s, 12.0s, 14.2s, 17.1s, 23.0s, 27.0s, 28.4s (m).
- **Average A-roll shot length ≈ 3.5s**, range 1.8–6s (m). R1 has one clean 6s run (17.1 → 23.0) with no cut at all — long takes are allowed, silence is not.
- Cuts land on **sentence / clause boundaries**, and they are frequently placed **mid-caption-card** (R3: cut between 1.6s and 2.6s while `any question in the world` stayed on screen). So subtitle boundaries and cut boundaries are independent — do not force them to align.
- No transitions of any kind: no crossfade, no whip, no zoom-punch, no speed ramp. Straight cuts only.

```
aroll_cut_rules:
  remove_silence_over: 250ms      # (e) tune here — this is the main lever
  min_shot_length: 1.5s
  target_avg_shot_length: 3.5s
  max_shot_length: 6s
  transition: hard_cut
  align_cuts_to_caption_boundaries: false
  reframe_between_cuts: false      # keep identical framing, it is meant to look like one take
```

### Overlays / b-roll (this is where the "cutting" energy actually lives)
Three distinct overlay treatments, all confined to the frame's upper half except the "hero" size:

1. **Corner PiP** — 9:16 clip, ~35% frame width, top-right, top edge ≈8% and bottom ≈42% of frame height, thin white border + soft shadow. Used for sourced social clips.
2. **Centred card** — 16:9 still or clip, ~60% frame width, centred, top third. Used for event photos, conference stages, and desktop/browser screen recordings.
3. **Hero card** — ~60–80% frame width, vertically centred, covering her torso. Used for the money shot (R1 @31s Carlton b-roll, R2's full phone screen-recordings). Subtitle still sits on top.

Swap rates (m):
- Rapid montage bursts: **one overlay every 0.4–0.6s** (R1: 9 swaps between 8.25s and 11.45s).
- Normal pacing: **one overlay every 1.5–3s** (R2: swaps at 4.3, 5.2, 5.5, 6.7, 8.2, 9.7, 11.2, 12.1, 13.8, 15.1, 16.8s → ~1.2s average through the evidence section).
- Full-frame b-roll cutaways (A-roll disappears entirely): **1.6s long**, used sparingly — R1 at 6.35–7.95s and 27.0–28.4s (m).

```
overlay_rules:
  slots: [corner_pip_9x16, centred_card_16x9, hero_card]
  region: upper_half   # except hero
  border: 2px white + drop shadow
  swap_interval_normal: 1.5-3s
  swap_interval_montage: 0.4-0.6s
  full_frame_cutaway_length: 1.6s
  z_order: aroll < overlay < subtitle
  entry: cut (no slide, no scale)
```

---

## 4. Hook card
- **White rounded pill behind each line**, bold near-black text, 2–3 lines, lines are different widths so the pills stagger. Slightly left of centre, sitting in the upper third above her head.
- On screen from **frame 0 to ~3.5–5s** (m: still present at 3.6s in R3 and 4.3s in R1, gone by 4.5s in R2), then hard cut off. No fade or slide in or out.
- Text is the thesis/provocation, not a label: `Stop trying to spot every AI video`, `Why AI isn't actually improving your workflow`, `Anthropic have agreed to answer your hard questions`.
- This is also the grid thumbnail, so it must be legible at thumbnail size — every reel on the profile uses it.

---


## 5. Priority order for the automation
1. Subtitle chunking + 1.0–1.5s cadence + fixed anchor + zero gaps. This is the most recognisable trait.
2. Silence-trim jump cuts to a ~3.5s average shot, straight cuts only, not aligned to caption boundaries.
3. Overlay slotting in the upper half with 1.5–3s swaps, and montage bursts at ~0.5s.
4. Hook pill card for the first ~4s.
