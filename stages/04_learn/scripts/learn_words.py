#!/usr/bin/env python3
"""
learn_words.py — notice which words you corrected, and propose the repeat
offenders for the lexicon.

    python3 stages/04_learn/scripts/learn_words.py <run-slug>

HOW IT KNOWS WHAT YOU CHANGED. `transcribe.py` writes the transcript twice:
`01-transcript.json`, which you edit, and `01-transcript-raw.json`, which nobody
touches. This compares them word by word. Every difference is something you
changed on purpose, because nothing else in the pipeline writes to either file.

THE PROMOTION TRIGGER IS "WRONG MORE THAN ONCE", AND THAT IS A TEST ACROSS RUNS.
A single run's diff can never satisfy it, which is why `memory/caption-fixes.md`
exists: the tally is the only thing that remembers a word was wrong last month
too. One correction is a typo or a one-off name. Two is a pattern, and a pattern
is worth biasing the next transcription toward.

IT NEVER WRITES `_config/lexicon.txt`. It proposes and waits. governance.md
rule 3.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import pipeline_lib as lib  # noqa: E402

PROMOTE_AT = 2  # "wrong more than once"

_ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$")
_STRIP = '.,!?";:\'()'


def changed_words(original: list[dict], corrected: list[dict]) -> list[tuple[str, str]]:
    """
    The (what you typed, what the model heard) pairs.

    Positional rather than fuzzy on purpose. A transcription fix is a same-slot
    substitution of one wrong word — the timings come from the audio and you are
    not retyping the take. A smarter diff would start inventing pairings that
    were never made, and those pairings would end up in the lexicon.
    """
    pairs = []
    for was, now in zip(original, corrected):
        heard = was["word"].strip(_STRIP)
        typed = now["word"].strip(_STRIP)
        if heard and typed and heard.lower() != typed.lower():
            pairs.append((typed, heard.lower()))
    return pairs


def load_tally(path: Path) -> dict:
    tally = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or "---" in line or line.startswith("| Term"):
            continue
        match = _ROW.match(line)
        if match:
            term, was, count, runs, promoted = match.groups()
            tally[term] = {
                "was": was,
                "count": int(count),
                "runs": [r.strip() for r in runs.split(",") if r.strip()],
                "promoted": promoted.strip(),
            }
    return tally


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: learn_words.py <run-slug>")
    slug = sys.argv[1]
    run = lib.run_dir(slug)

    raw_path = run / "01-transcript-raw.json"
    if not raw_path.exists():
        sys.exit(
            f"no 01-transcript-raw.json in {lib.RUNS_REL}/{slug}/.\n"
            "  Without the original there is nothing to compare your edits against.\n"
            "  transcribe.py writes it on the first run and never overwrites it."
        )

    original = lib.read_json(raw_path)["words"]
    corrected = lib.read_json(lib.require(run / "01-transcript.json", "transcribe.py"))["words"]

    # Words added or removed rather than corrected in place put every position
    # after that point out of step, so a word-for-word comparison would report
    # pairings nobody made. Stopping is right — a wrong lexicon entry is worse
    # than a missed one, because it biases every future transcription.
    if len(original) != len(corrected):
        print(f"  ! the transcript has {len(corrected)} words, the original had "
              f"{len(original)}.")
        print("    Words were inserted or deleted, not corrected in place, so the")
        print("    comparison would be misaligned from that point on. Nothing tallied.")
        return

    fixes = changed_words(original, corrected)

    tally_path = lib.MEMORY_DIR / "caption-fixes.md"
    tally = load_tally(tally_path)
    already_in_lexicon = {t.lower() for t in lib.load_lexicon()}

    if not fixes:
        print("  no corrections in this run — nothing to tally")

    corrected_here = set()
    for correct, wrong in fixes:
        entry = tally.setdefault(correct, {"was": wrong, "count": 0,
                                           "runs": [], "promoted": ""})
        # The count is runs, not occurrences. A word you fixed in six places in
        # one take was still wrong once, and counting the occurrences would
        # promote it off the back of a single run.
        if slug not in entry["runs"]:
            entry["count"] += 1
            entry["runs"].append(slug)
        if wrong not in entry["was"]:
            entry["was"] += f" / {wrong}"
        corrected_here.add(correct)

    newly_at_threshold = [
        (term, tally[term]) for term in sorted(corrected_here)
        if tally[term]["count"] >= PROMOTE_AT
        and not tally[term]["promoted"]
        and term.lower() not in already_in_lexicon
    ]

    if fixes:
        print(f"  {len(corrected_here)} words corrected, in {len(fixes)} places:")
        for term in sorted(corrected_here):
            places = sum(1 for correct, _ in fixes if correct == term)
            print(f"    heard {tally[term]['was']!r} -> you wrote {term!r}"
                  + (f"  ({places} places)" if places > 1 else ""))

    header = tally_path.read_text(encoding="utf-8").split("| Term")[0].rstrip()
    lines = [header, "",
             "| Term (corrected to) | Was transcribed as | Count | Runs | Promoted |",
             "|---|---|---|---|---|"]
    for term, entry in sorted(tally.items()):
        lines.append(f"| {term} | {entry['was']} | {entry['count']} | "
                     f"{', '.join(entry['runs'])} | {entry['promoted']} |")
    tally_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  memory/caption-fixes.md — {len(tally)} terms tracked")

    # ---- propose, never write ------------------------------------------
    if not newly_at_threshold:
        print(f"  nothing corrected in {PROMOTE_AT} separate runs yet — no proposal")
        return

    proposal = run / "04-proposed-words.md"
    block = [f"# Proposed for the lexicon — {slug}", "",
             f"These words have now been corrected in {PROMOTE_AT} or more separate runs.",
             "Adding one to `_config/lexicon.txt` biases the next transcription toward it,",
             "so it stops coming out wrong.", "",
             "**Nothing has been written.** Copy across the ones you want.", ""]
    for term, entry in newly_at_threshold:
        block.append(f"- [ ] `{term}`  — heard as *{entry['was']}* "
                     f"in {entry['count']} runs ({', '.join(entry['runs'])})")
    block.append("")
    proposal.write_text("\n".join(block), encoding="utf-8")

    print(f"\n  {len(newly_at_threshold)} words PROPOSED for _config/lexicon.txt:")
    for term, entry in newly_at_threshold:
        print(f"    {term}  (heard as {entry['was']}, {entry['count']} runs)")
    print(f"  written to {lib.RUNS_REL}/{slug}/04-proposed-words.md — nothing added yet.")


if __name__ == "__main__":
    main()
