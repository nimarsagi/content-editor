---
name: learn
type: process
universe: live
status: verified
verified: 2026-08-26
consumes: [transcript, lexicon, tallies]
produces: [tallies]
---

# Learn

**Input →** the corrections you made to a run's transcript. **Movement →** compare the two transcripts, tally across runs. **Output →** an updated tally, and a lexicon proposal once a word has been wrong twice.

```
python3 stages/04_learn/scripts/learn_words.py <slug>
```

**Not part of a run.** Nothing waits for it, nothing downstream depends on it, and `caption.py` never calls it.

## Steps

1. `learn_words.py:79-85` — require `01-transcript-raw.json`. Without the original there is nothing to compare against.
2. `learn_words.py:94-99` — if the two word counts differ, **stop and tally nothing**. Words were inserted or deleted rather than corrected in place, so every position after that is out of step and the comparison would report pairings nobody made.
3. `changed_words` (`:38-53`) — positional, never fuzzy. A transcription fix is a same-slot substitution; a smarter diff would invent pairings that end up in the lexicon, biasing every future transcription toward a word you never said.
4. `learn_words.py:110-122` — increment **once per run**, not per occurrence. A word fixed six times in one video was wrong once.
5. `learn_words.py:138-146` — rewrite `memory/caption-fixes.md`, preserving its header verbatim.
6. `learn_words.py:149-168` — terms at 2+ runs, not already promoted, not already in the lexicon → `04-proposed-words.md`. **Nothing is written to `_config/`.**

## Why the threshold is two runs

One correction is a typo or a one-off name. Two is a pattern — and that is a test *across* runs, which is why the tally is a file and not a variable.

## If you change this

**Hits**
- **Lowering `PROMOTE_AT`** (`learn_words.py:32`) makes single typos into lexicon proposals. A wrong entry is worse than a missing one.
- **Making the diff fuzzy** is the change this design most explicitly refuses. Read the docstring at `:39-45` first.
- **Skipping step 3 of the fix-a-word loop** is the common failure — the word gets fixed in the video and comes back wrong next time.

**Does not hit**
- **`_config/lexicon.txt`.** It proposes and waits (`governance.md` rule 2 — the docstring's "rule 3" at `learn_words.py:20` is a miscitation).
- **The current run's output.** Nothing here re-renders anything.

## See

`stages/04_learn/scripts/learn_words.py` · `stages/04_learn/CONTEXT.md` · `identity.md`, "What it learns"
