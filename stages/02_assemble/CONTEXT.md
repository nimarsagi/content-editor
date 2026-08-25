# 02_assemble — stage contract

**Takes** the transcript.
**Gives back** caption cards that obey the duration and width rules, plus an `.srt` sidecar.

```
   chunk_captions.py  ->  write_srt.py
```

---

## Inputs

| Input | Level | Used by |
|---|---|---|
| `01-transcript.json` | **L4 — this run** | `chunk_captions.py` |
| `_config/edit-defaults.yaml` | L3 — stable | both |
| `memory/preferences.md` § Pacing | L3 — stable | `chunk_captions.py` |

## Outputs

| File | Written by |
|---|---|
| `02-caption-cards.json` | `chunk_captions.py` |
| `02-captions.srt` | `write_srt.py` |

---

## The ordering that makes this correct

**The video was cut before it was transcribed**, in CapCut, and that is why the captions line up — the argument is in `CLAUDE.md`, *The one thing every component has to know*.

**Nothing in this stage removes anything.** Filler sounds, pauses, a sentence started twice — if it survived your edit, it gets captioned. A chunker that dropped "uhm" would be editing your speech (`governance.md` rule 1).

---

## Four rules inside the chunker

1. **Duration is the rule.** Words per card and reading speed are diagnostics — measured, printed, enforced by nothing. They cannot all be rules: captions track speech exactly, so a card's duration is words divided by speech rate, not a free choice.
2. **Prefer the fewest cards** that satisfy the duration window. A chunker that splits at every legal boundary produces perfect timings and a frantic result.
3. **Never strip or auto-balance quotes.** Reported speech opens on one card and closes several cards later; balancing per card corrupts the text.
4. **Hold a card until the next one starts — but never past the ceiling.** The holding is what stops captions flickering off in the beat between two phrases. The ceiling is what stops a pause you left in for emphasis having the previous sentence sit on top of it.
5. **Join a card that would flash — when it fits.** A card under the 0.6s floor is joined into the card before it. Because cards run wall-to-wall, that is the only move available: a short card cannot be held longer, so the only way to lift it over the floor is to give it more words. The join is refused when the result overruns the row, which at 25 characters is most of the time — on the 2026-07-30 run, 2 of 10 could be joined. The other 8 are reported, not called bugs. A second row is the only lever that would clear them.

Rule 4 used to be unreachable, because a cutting stage removed every silence before the captions were built. With the cutting done by hand in CapCut, whatever pauses you kept are still there when this runs.

---

## The wrapper returns None, and that matters

A line break has to land between two words, so a card's real capacity is not `chars_per_line × max_lines` — it is whatever the word boundaries allow, which is always less and sometimes much less.

At the current one-row config that shows up plainly: the budget is 25 characters, and "so the thing about pricing that" runs to 26 by the time "pricing" is added, so the card has to close after "about". It bit harder under the old two-row config — the same phrase is 31 characters and fits in 34, yet the only splits available are 2/28, 6/24, 12/18 and 18/12, none of which leaves both halves under 17. Worth keeping in view if `max_lines` ever goes back to 2.

`wrap()` returns `None` for a card it cannot lay out, and callers must read that as *close this card earlier*, never as a reason to cut a word in half. An earlier version sliced at the character count and shipped `"so the thing abou"` / `"t pricing that"`.
