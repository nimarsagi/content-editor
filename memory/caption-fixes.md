# caption-fixes.md — every caption term the person has corrected

Exists for one reason: the lexicon promotion rule is *"wrong more than once"*, and that is a test across runs. A single run's diff can never satisfy it. This file is the memory that makes the count possible — the only thing that remembers a word was wrong last month too.

Written by `learn_words.py`. It compares `01-transcript.json` against `01-transcript-raw.json`, finds the words you corrected, and increments their counts. **At count ≥ 2 it proposes the term for `_config/lexicon.txt`** — it never writes there directly (`governance.md` rule 2).

The count is **runs, not occurrences.** A word you fixed six times in one video was still only wrong once.

---

| Term (corrected to) | Was transcribed as | Count | Runs | Promoted |
|---|---|---|---|---|

*(empty — no runs yet)*
