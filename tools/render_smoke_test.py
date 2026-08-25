#!/usr/bin/env python3
"""
render_smoke_test.py — prove the caption render works, without transcribing.

    python3 tools/render_smoke_test.py <any-video-file>

Fabricates a transcript with evenly spaced words over the video's real duration,
then runs the same steps a real run does from there on — chunking, srt, render.
Nothing about the render path is faked: the geometry assertion, the config-driven
style, the font, the props and Remotion itself all run for real.

WHAT IT PROVES: that a video goes in and a captioned video comes out, with the
cards where the config says they go.

WHAT IT DOES NOT PROVE: that the words are right. Transcription is a separate
question and needs faster-whisper and real audio.

Use a SHORT clip. Rendering is per-frame, so a five-second test costs seconds
and a two-minute one costs minutes.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pipeline_lib as lib  # noqa: E402

SLUG = "smoke"

# Deliberately awkward: long words that force a line break, short ones that do
# not, and no punctuation anywhere — so every split is decided by the width
# budget rather than a clause boundary. That is the path where caption bugs live.
SCRIPT = (
    "so the thing about pricing that nobody actually tells you is that your "
    "first number is almost always too low and the reason for that is simple "
    "you are pricing your time instead of pricing the outcome"
).split()


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    video = Path(sys.argv[1]).expanduser().resolve()
    if not video.is_file():
        sys.exit(f"not a file: {video}")

    duration = lib.probe_duration(video)
    fps = lib.probe_frame_rate(video)
    print(f"  video       {video.name}  {lib.timecode(duration)} @ {fps:.3f}fps")

    run = lib.run_dir(SLUG, create=True)

    # Words spread evenly across the whole clip, leaving a little air at each
    # end so the first and last card are not clipped by the video's edges.
    head, tail = 0.3, 0.3
    speaking = max(duration - head - tail, 0.5)
    step = speaking / len(SCRIPT)
    words = [
        {
            "word": word,
            "start": round(head + index * step, 3),
            "end": round(head + (index + 1) * step - 0.01, 3),
            "probability": 0.99,
        }
        for index, word in enumerate(SCRIPT)
    ]

    lib.write_json(run / "01-transcript.json", {
        "topic": "smoke test — pricing your work",
        "video": str(video),
        "duration": duration,
        "fps": fps,
        "words": words,
    })
    (run / "01-topic.md").write_text("smoke test — pricing your work\n", encoding="utf-8")

    steps = [
        "stages/02_assemble/scripts/chunk_captions.py",
        "stages/02_assemble/scripts/write_srt.py",
        "stages/03_render/scripts/render_captions.py",
    ]
    for script in steps:
        print(f"\n--- {Path(script).name} " + "-" * (40 - len(Path(script).name)))
        sys.stdout.flush()
        if subprocess.run([sys.executable, str(lib.ROOT / script), SLUG]).returncode != 0:
            sys.exit(f"\n  stopped at {Path(script).name}.")


if __name__ == "__main__":
    main()
