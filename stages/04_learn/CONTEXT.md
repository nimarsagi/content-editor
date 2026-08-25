# 04_learn — stage contract

**Takes** the corrections you made to a run's transcript.
**Gives back** a tally that survives across runs, and a lexicon proposal once a word has been wrong twice.

**This stage is not part of a run.** It is what you do afterwards, when you noticed a word came out wrong. Nothing waits for it and nothing downstream depends on it.

---

## Inputs

| Input | Level | Notes |
|---|---|---|
| `01-transcript.json` | **L4 — this run** | your version, with the fixes in it |
| `01-transcript-raw.json` | **L4 — this run** | what the model actually heard |
| `_config/lexicon.txt` | L3 — stable | read only, to skip words already in it |
| `memory/caption-fixes.md` | L3 — stable | the running tally. Read, updated, rewritten. |

## Outputs

| File | Written by |
|---|---|
| `memory/caption-fixes.md` | `learn_words.py` — a record, not a decision |
| `04-proposed-words.md` | `learn_words.py` — **approval gate** |

---

## How it knows what you changed

It compares the two transcripts word by word. Every difference is something you changed on purpose, because nothing else in the pipeline writes to either file.

**The comparison is positional, not fuzzy.** A transcription fix is a same-slot substitution of one wrong word — the timings come from the audio and you are not retyping the take. A smarter diff would start inventing pairings that were never made, and those pairings would end up in the lexicon, biasing every future transcription toward a word you never said.

If the two files have different word counts, someone inserted or deleted words rather than correcting them in place. Every position after that point is out of step, so the comparison stops and says so rather than reporting nonsense.

---

## Why the threshold is two runs

**One correction is a typo or a one-off name. Two is a pattern.**

The trigger is *"wrong more than once"*, and that is a test across runs — a single run's diff can never satisfy it. `memory/caption-fixes.md` is the only thing that remembers a word was wrong last month too, which is why the tally is a file and not a variable.

**Counted in runs, never in occurrences.** A word you fixed six times in one video was still only wrong once; counting occurrences would promote it off the back of a single take.

## It never writes the lexicon

It writes `04-proposed-words.md` with a checklist and stops. You copy across the ones you want. `governance.md` rule 2.
