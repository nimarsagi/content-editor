---
name: lexicon
type: object
cluster: dials
universe: live
status: verified
verified: 2026-08-26
---

# Lexicon

`_config/lexicon.txt` — terms that seed transcription, so proper nouns and the words you actually use stop coming out wrong. Plain lines; `#` comments and blanks ignored (`pipeline_lib.py:83-93`).

## Why this shape

**It is the only thing this tool learns.** The cut-proposal loop is gone; the words survived (`identity.md`, "What it learns").

**Nothing writes it.** `learn_words.py:153-163` writes `04-proposed-words.md` with a checklist and stops; you copy across what you want. `governance.md` rule 2 — and note that the docstring at `learn_words.py:19-20` cites "rule 3", which is the raw-transcript rule. The behaviour is right; the citation is off by one.

**The promotion threshold is two separate runs, counted in runs and never in occurrences** (`learn_words.py:32`, `:117-119`). A word fixed six times in one video was wrong once. One correction is a typo; two is a pattern.

## Shape

One term per line. Reaches the model through `build_prompt()` (`transcribe.py:40-53`) as `"Terms used in it: …"`, alongside the run's topic.

The proposal file lists each term with what it was heard as and which runs it was wrong in (`learn_words.py:159-161`).

## Connected to

- **read by** — `transcribe.py:85`, and `learn_words.py:105` to skip words already in it
- **proposed into by** — [[learn]], via `04-proposed-words.md`
- **counted in** — [[tallies]] → `memory/caption-fixes.md`
- **looks like but is not** — the topic. Both seed the same prompt, but the topic is per run and required; the lexicon is stable and optional.

## If you change this

**Hits**
- **Adding a term biases every future transcription toward it.** That is the point, and it is also why a wrong entry is worse than a missing one — it would push the model toward a word you never said.
- **Adding a term does not fix past runs.** Re-transcribing an existing run is exactly what `--redo` refuses to do.
- **`_config/` is in `CHECK_DIRS`** (`tools/sync.py:34`), so an edit here runs the fixture checks.

**Does not hit**
- **Existing transcripts, cards, or renders.** Nothing downstream reads the lexicon.
- **The tally.** `caption-fixes.md` keeps counting a term after it is promoted; the `Promoted` column is what stops it being proposed twice (`learn_words.py:127`).

## Surfaces

Hand-edited by the person, on an explicit yes. Read by `transcribe.py` and `learn_words.py`.

## See

`_config/lexicon.txt` · `stages/04_learn/scripts/learn_words.py:148-168` · `stages/04_learn/CONTEXT.md`
