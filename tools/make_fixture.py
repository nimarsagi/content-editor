#!/usr/bin/env python3
"""
make_fixture.py — a synthetic transcript, for testing without footage.

Stands in for a finished CapCut export that has already been transcribed. It
exercises the cases that actually break the caption chunker:

  - NO PUNCTUATION ANYWHERE, so every split is forced by the text budget rather
    than chosen at a clause boundary. That is the harder path through
    build_cards, and it is where a real defect was found.
  - a short pause mid-sentence, which is a legal split point
  - A PAUSE LONGER THAN THE CAPTION CEILING, left in on purpose for emphasis.
    Cards are stretched to meet the next one so captions do not flicker between
    phrases, and this is the case where that stretching has to stop: the
    previous sentence must not sit on screen for the whole silence.
  - filler sounds left in the speech. Nothing here removes them — the video was
    cut by hand before it arrived — so they must appear in the captions. A
    chunker that quietly dropped them would be rewriting what was said.
  - a final card short enough to fall under the duration floor on its own

    python3 tools/make_fixture.py
    python3 tools/run_fixture_checks.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pipeline_lib as lib  # noqa: E402

SLUG = "fixture"


def say(text, start, rate=0.33, gaps=None):
    """Lay words out at roughly 180wpm, with optional pauses after a word."""
    gaps = gaps or {}
    out, t = [], start
    for index, word in enumerate(text.split()):
        out.append({"word": word, "start": round(t, 3), "end": round(t + rate, 3),
                    "probability": 0.95})
        t += rate + gaps.get(index, 0.02)
    return out


def main():
    run = lib.run_dir(SLUG, create=True)

    words = []
    words += say("So the thing about pricing that nobody uhm actually tells you",
                 0.4, gaps={7: 0.9})
    # a 3.2s beat left in on purpose — longer than the 2.5s caption ceiling
    words += say("is that your first number is almost always too low", 8.8)
    words += say("ehh and the reason for that is simple you are pricing your time",
                 16.5)

    lib.write_json(run / "01-transcript.json", {
        "topic": "pricing your work as a consultant",
        "video": "/fake/capcut-export.mp4",
        "duration": 22.5,
        "fps": 30.0,
        "words": words,
    })
    (run / "01-topic.md").write_text(
        "pricing your work as a consultant\n", encoding="utf-8")

    print(f"  {len(words)} words over 26.0s, one finished video")
    print(f"  run: {lib.RUNS_REL}/{SLUG}/")
    print("  next: python3 tools/run_fixture_checks.py")


if __name__ == "__main__":
    main()
