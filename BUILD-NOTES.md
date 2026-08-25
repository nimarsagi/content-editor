# Build notes — what is verified, what is not

Built 2026-07-27 from `architecture-thinking-partner/output/build-spec-content-editor.md` (status `ready`) and its ratified ADRs. **Reduced to the captioning-only shape on 2026-07-29**, when DaVinci Resolve was dropped.

This file records **what was actually tested and what was not**, so nobody has to guess later which parts have been exercised.

---

## What changed on 2026-07-29 — the canonical account

**This section is the one place the Resolve removal is written down.** `identity.md`, `governance.md`, `CONTEXT.md`, `memory/preferences.md` and `_config/edit-defaults.yaml` each point here rather than retelling it, because those files load on every session and this one does not.

Resolve is gone. The cutting happens by hand in CapCut, and this workspace captions the finished export.

Removed, and recoverable from the commit tagged in git history immediately before: the cut-proposal stage, the marker-based review loop, the supervised/unsupervised mode split, the timeline builder, the Resolve renderer, and the three Resolve-host workarounds (symlinks it would not execute, swallowed output, an ASCII-only interpreter).

**Both model call sites went with it** — one judged whether a stretch rambled, the other interpreted review notes. Both belonged to the cut-proposal stage. A run now costs local transcription and nothing else, and the fixture checks assert there are no model call sites, so a new one has to be added on purpose rather than sliding in.

### Why it cannot come back

The original design was an iterative learning loop, in the person's words:

> *"I prefer to approve them the first few times and that you learn from what I like. Once you're highly consistent with the way I like the output to be, then I want you to cut-up the video that's basically done. So we start with an iterative learning process."*

Two governance rules existed to run it: a supervised/unsupervised mode split, and a marker-based review where the tool proposed cuts onto a Resolve timeline and read your verdicts back off it. **Both halves needed a timeline the tool could write to and read from.** CapCut has no scripting interface, so there is nowhere to send a proposal and no way to see what you decided about one.

The same loss took the rule-proposing half of `memory/preferences.md`: the loop that used to draft pacing rules read your notes off that timeline. You now write that file by hand.

**This was a deliberate trade, not an oversight.** The north star it still serves is the narrower half — *"an annoying chore off my plate"*. The captioning is off the plate; the cutting is not, and under this design it will not be. Worth knowing before anyone tries to restore the learning loop by bolting a cut-proposal stage back on.

**What survived, deliberately:** the tool still learns the words it gets wrong. That loop never needed Resolve — it needs a before-and-after comparison, which is why `transcribe.py` writes the transcript twice.

---

## Verified — run and checked

`python3 tools/sync.py` — 15 assertions, all passing.

| What | Result |
|---|---|
| Every spoken word reaches a caption | held — 34 spoken, 34 captioned |
| Filler sounds are kept, not silently dropped | held. Nothing here cuts; dropping "uhm" would be editing the speech |
| Caption rules — ceiling, line width, max lines | all hold |
| Every under-floor card that could be joined, was | held — see *The floor cannot always be met* below |
| Cards run in order and never overlap | held |
| A card holds until the next one starts | held |
| **A silence longer than the ceiling is left uncaptioned** | held — see the defect below |
| The geometry arithmetic (safe margins, derived character budget) | held |
| The `.srt` has one block per card | held |
| No model call sites anywhere under `stages/` | held |
| No pipeline script mentions Resolve | held |
| The source specs stay unread by any runtime code path | held |
| Every script compiles | held |

### The removal was proved to be a no-op where it had to be

The caption chunker carried machinery for clip breaks — the joins between burst-filmed clips, which must never be a caption split. With one already-assembled video there are no breaks, so that code was inert. **Before removing it, its output was captured on a no-breaks input and compared afterwards: byte-identical, 10 cards.** The removal changed nothing; it only stopped the file describing a concept that no longer exists anywhere in the workspace.

### One real defect, found by removing the cut stage

**A caption could sit on screen through an arbitrarily long silence.** Cards are stretched to meet the next one so they do not flicker off between phrases — with no bound, a 5-second pause left the previous sentence on screen for all 5 seconds, three times over the 2.5s ceiling.

This was unreachable before, because the cut stage removed every silence before the captions were built. With the cutting done by hand, whatever pauses you kept are still there. The stretch is now bounded by the ceiling: past that the video is genuinely silent and the screen goes clean.

### The floor cannot always be met, and that is now explicit

**Found 2026-07-31, on the first real run.** Ten of 84 cards sat under the 0.6s floor and the chunker never checked for it — `build_cards` reads the ceiling and the text budget and nothing else, so it produced the violation and then reported it as a bug.

It cannot simply be enforced. Cards run wall-to-wall, so a short card cannot be held past the card after it. The only move is to join it into the card before, and at one row of 25 characters that usually overruns the frame:

| | |
|---|---|
| under the floor | 10 of 84 |
| joinable — joined | 2 (`'which it cannot do.'`, `'a comment, let me know'`) |
| not joinable | 8, coming to 29–41 characters against a 25-character row |

Joining the first of those also cleared the run's one dangling card, since `'which it'` no longer ends a caption.

Two dead ends worth recording, so nobody re-walks them. **Moving the split earlier** instead of joining looked like it fixed 5 more, but four of those ended a card on *of*, *has*, *you* or *and* — it was trading the floor against `never_end_card_on`. With that rule respected it fixes one. **A smaller font** would buy room, but fitting even the smallest failing join needs 38px, below the 40px legibility floor.

So the remaining 8 are the standing cost of one row at 44px — the trade made on 2026-07-30, which already cut this from 39 under the floor at 62px. They are reported, not flagged as bugs, because an error nobody can act on is noise. **A second row is the only lever that clears them.**

### The learning loop fires

Tested across two runs where the model heard "prizing" for "pricing":

- run 1 — tallied, **no proposal** (one run is not a pattern)
- run 2 — proposed `pricing` for the lexicon, once, naming both runs
- `_config/lexicon.txt` **not written**

A duplicate-proposal defect was found and fixed on the way: the word appeared twice in the transcript, so it was proposed twice. The count is runs, not occurrences.

---

## Repeatable checks

```
python3 tools/sync.py                       syntax + the checks
python3 tools/render_smoke_test.py <clip>   the real render path, on a short clip
```

The fixture is a synthetic transcript standing in for a finished export: no punctuation anywhere, so every caption split is forced by the text budget rather than chosen at a clause boundary; a short pause mid-sentence; a 3.2s beat left in on purpose, longer than the ceiling; filler sounds; and a final card short enough to fall under the duration floor on its own.

`render_smoke_test.py` runs the render path for real — the geometry assertion, the config-driven style, the font, the props, and Remotion itself. It does not prove the words are right.

---

## NOT verified

- **Transcription.** `faster-whisper` is not installed yet and no real audio has been through it. Word-level timestamps are a hard requirement; `transcribe.py` aborts loudly without them, but that check has never fired for real.
- **The render.** Remotion has never rendered a frame here. `render_smoke_test.py` exists to answer this in one command against a short clip, and has not been run.
- **The safe zone.** The margins are a conservative envelope from third-party guides that vary by up to 330px on some edges, not a published platform spec. Only an export with the safe zone checked on-device, in both apps, closes this. No code can.
- **Caption sync at the end of a long take.** The frame-rate handling is careful about 29.97 specifically because this is where drift shows. Never measured on a real two-minute video.
- **The lexicon closing its loop on real audio.** The mechanism is proven on synthetic data. Whether the words *you* actually get wrong are the kind a bias prompt fixes is a different question.

---

## One structural addition beyond the spec

`pipeline_lib.py` at the workspace root — config loading, preference overrides, run-folder paths, and the ffprobe calls, written once instead of five times. It is engine, it holds no thresholds and no paths of its own, and it only reads `_config/`. The build spec's folder map does not name it; it is a deviation from the baseline and it is here rather than hidden.

`tools/` likewise: `sync.py` is a development convenience and the fixture pair is the regression suite. None of them is part of a run.
