#!/usr/bin/env python3
"""
write_srt.py — the .srt sidecar.

Produced on every run as a byproduct of the same caption data, not as a
conditional feature. Nothing downstream needs it — Remotion burns the captions
on from the cards, not from this file — and it is written anyway, because it is
the one caption artifact that outlives this workspace. It opens in anything, it
uploads to any platform that takes a subtitle file, and if you ever want the
captions on a video this pipeline did not make, this is what you carry over.

Word-level timing does not survive .srt, but the display is phrase-chunked
anyway, so nothing that reaches the screen is lost.

    python3 stages/02_assemble/scripts/write_srt.py <run-slug>
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import pipeline_lib as lib  # noqa: E402


def srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: write_srt.py <run-slug>")
    slug = sys.argv[1]
    run = lib.run_dir(slug)

    data = lib.read_json(lib.require(run / "02-caption-cards.json", "chunk_captions.py"))
    cards = data["cards"]

    blocks = []
    for number, card in enumerate(cards, start=1):
        # The line breaks are carried through as real newlines. They were
        # computed against the frame's width budget, so an .srt consumer that
        # re-wraps will produce something wider than the safe zone allows.
        text = "\n".join(card["lines"])
        blocks.append(
            f"{number}\n"
            f"{srt_time(card['start'])} --> {srt_time(card['end'])}\n"
            f"{text}\n"
        )

    path = run / "02-captions.srt"
    path.write_text("\n".join(blocks), encoding="utf-8")
    print(f"  wrote {lib.RUNS_REL}/{slug}/02-captions.srt  ({len(cards)} cards)")


if __name__ == "__main__":
    main()
