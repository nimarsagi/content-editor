#!/usr/bin/env python3
"""
make_fixture_video.py — a short synthetic export, for testing the whole chain.

    python3 tools/make_fixture_video.py

make_fixture.py stands in for a video that has already been transcribed. This
stands in for the video itself: a real file with real speech on it, so the steps
that open media — read_video, transcribe, calibrate, render — can be exercised
without spending two minutes on a real take.

WHAT IT IS BUILT TO LOOK LIKE. A CapCut export: several clips butted together,
each its own recording, each at its own level. That is the shape the audio work
exists for, so the fixture has it on purpose:

  - THREE CLIPS AT THREE DIFFERENT LEVELS, 12 dB apart end to end. Levelling has
    something real to correct, and "the spread is narrower out than in" is a
    number a script can check rather than an impression.
  - THE LAST CLIP DRIFTS DOWN as it runs, the way a sentence does when the
    breath runs out. Within-clip correction has something real to flatten.
  - A CUT INSIDE A SILENCE. Each clip ends with a beat before the next begins,
    so the picture change lands in a gap between words — which is where a cut
    lands in a real edit, and where a boundary is allowed to snap to.
  - A DIFFERENT SOLID COLOUR PER CLIP, so the cuts are unmissable to a scene
    detector. The fixture is not trying to be hard; it is trying to be KNOWN.

    THE COLOURS DIFFER IN BRIGHTNESS, NOT JUST IN HUE, and that is not a
    decoration. ffmpeg's scene detection works on luma, so two clips that are
    obviously different colours on screen can be invisible to it: an earlier
    version of this fixture used a red and a green that both landed near luma
    72, and the cut between them scored 0.020 — under the threshold, silently
    missed. That is a real case (a jump cut at the same framing measured 0.005
    on a real video), and the real videos are where it belongs. Here it only
    made the known answer wrong.

The truth is written beside it. Nothing in the pipeline reads that file — it is
for a test to grade against, the same way source-specs are provenance for a
human and not an input to a run.

HEVC AND 44.1 kHz, because that is what the real exports are (checked: both
videos in input/ are hevc / aac 44100 / 2ch / 1080x1920 @ 30fps). A fixture in
a friendlier codec would skip the renderer's transcode path, which is a path
that has broken before.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pipeline_lib as lib  # noqa: E402

FIXTURE_DIR = lib.ROOT / "tools" / "fixtures"
VIDEO = FIXTURE_DIR / "endtoend.mov"
TRUTH = FIXTURE_DIR / "endtoend-truth.json"

TOPIC = "pricing your work as a consultant"

# Deliberately awkward for the chunker, the same way the synthetic transcript is:
# no punctuation, so every caption split is forced by the width budget.
#
# The levels are the point. -26 / -14 / -20 dBFS mean is a 12 dB spread, wider
# than the 6-9 dB measured across the real reels, so a levelling pass that does
# nothing is impossible to mistake for one that works.
CLIPS = [
    {
        "text": "So the thing about pricing that nobody actually tells you",
        "level_dbfs": -26.0,
        "drift_db": 0.0,
        "colour": "0x101828",      # luma  23
        "gap_s": 0.5,
    },
    {
        "text": "is that your first number is almost always too low",
        "level_dbfs": -14.0,
        "drift_db": 0.0,
        "colour": "0x9A6B2B",      # luma 114
        "gap_s": 0.6,
    },
    {
        "text": "and the reason for that is simple you are pricing your time",
        "level_dbfs": -20.0,
        "drift_db": 5.0,          # falls 5 dB from first word to last
        "colour": "0xD8D0C0",      # luma 209
        "gap_s": 0.4,
    },
]

WIDTH, HEIGHT, FPS = 1080, 1920, 30
SAMPLE_RATE, CHANNELS = 44100, 2

_MEAN_VOLUME = re.compile(r"mean_volume:\s*(-?[\d.]+) dB")


def run(cmd: list[str], what: str) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"{what} failed:\n{result.stderr.strip()}")
    return result


def speak(text: str, out: Path) -> None:
    """macOS speech synthesis. Real words, no microphone, no network."""
    # BEI16, not LEI16 — AIFF is a big-endian container and `say` rejects the
    # little-endian form with an unhelpful "fmt?".
    run(["say", "-o", str(out), "--data-format=BEI16@44100", text], "say")


def mean_volume(audio: Path) -> float:
    """Mean level in dBFS, via ffmpeg's own meter. The reference for levelling."""
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(audio), "-af", "volumedetect",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    match = _MEAN_VOLUME.search(result.stderr)
    if not match:
        sys.exit(f"could not measure {audio.name} — volumedetect printed no mean_volume")
    return float(match.group(1))


def build_clip(clip: dict, source: Path, out: Path) -> float:
    """One clip: solid colour, speech at its own level, then a beat of silence."""
    speech_s = lib.probe_duration(source)
    total_s = speech_s + clip["gap_s"]

    # Two passes, because the level has to be known before it can be set.
    gain_db = clip["level_dbfs"] - mean_volume(source)

    filters = [f"volume={gain_db:.3f}dB"]
    if clip["drift_db"]:
        # A linear fall in dB across the speech, so the correction has a straight
        # line to find. Commas escaped — ffmpeg splits filter arguments on them.
        filters.append(
            f"volume=eval=frame:volume='pow(10\\, "
            f"(-{clip['drift_db']:.3f}*min(t\\,{speech_s:.3f})/{speech_s:.3f})/20)'"
        )
    filters.append(f"apad=whole_dur={total_s:.3f}")
    filters.append(f"aformat=sample_rates={SAMPLE_RATE}:channel_layouts=stereo")

    run([
        "ffmpeg", "-v", "error", "-y",
        "-f", "lavfi", "-i",
        f"color=c={clip['colour']}:s={WIDTH}x{HEIGHT}:r={FPS}:d={total_s:.3f}",
        "-i", str(source),
        "-af", ",".join(filters),
        "-c:v", "libx265", "-preset", "ultrafast", "-crf", "30",
        "-pix_fmt", "yuv420p", "-tag:v", "hvc1",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(out),
    ], f"building clip {out.name}")

    return total_s


def main():
    if sys.platform != "darwin":
        sys.exit("make_fixture_video.py uses macOS `say` for speech. "
                 "On another platform, supply a short real export instead.")

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    work = FIXTURE_DIR / ".work"
    work.mkdir(exist_ok=True)

    parts, boundaries, elapsed = [], [], 0.0
    for index, clip in enumerate(CLIPS, start=1):
        speech = work / f"clip{index}.aiff"
        piece = work / f"clip{index}.mov"
        speak(clip["text"], speech)
        length = build_clip(clip, speech, piece)
        parts.append(piece)

        speech_s = lib.probe_duration(speech)
        boundaries.append({
            "clip": index,
            "starts_at_s": round(elapsed, 3),
            "ends_at_s": round(elapsed + length, 3),
            "speech_ends_at_s": round(elapsed + speech_s, 3),
            "level_dbfs": clip["level_dbfs"],
            "drift_db": clip["drift_db"],
            "text": clip["text"],
        })
        elapsed += length
        print(f"  clip {index}      {length:5.2f}s  at {clip['level_dbfs']:+.1f} dBFS"
              + (f", drifting -{clip['drift_db']:.0f} dB" if clip["drift_db"] else ""))

    listing = work / "concat.txt"
    listing.write_text(
        "".join(f"file '{p.name}'\n" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
         "-i", str(listing), "-c", "copy", str(VIDEO)], "concatenating clips")

    levels = [c["level_dbfs"] for c in CLIPS]
    TRUTH.write_text(json.dumps({
        "note": "Ground truth for tools/endtoend.mov. Provenance for tests — "
                "no pipeline script reads this.",
        "topic": TOPIC,
        "video": VIDEO.name,
        "duration_s": round(elapsed, 3),
        "sample_rate": SAMPLE_RATE,
        "channels": CHANNELS,
        "clip_spread_db": round(max(levels) - min(levels), 3),
        "cuts_at_s": [c["starts_at_s"] for c in boundaries[1:]],
        "clips": boundaries,
    }, indent=2) + "\n", encoding="utf-8")

    for leftover in work.iterdir():
        leftover.unlink()
    work.rmdir()

    print(f"\n  {VIDEO.relative_to(lib.ROOT)}  "
          f"{lib.timecode(lib.probe_duration(VIDEO))}, "
          f"{VIDEO.stat().st_size / 1e6:.1f} MB")
    print(f"  {len(CLIPS)} clips, {max(levels) - min(levels):.0f} dB apart, "
          f"cuts at {', '.join(f'{c:.2f}s' for c in [b['starts_at_s'] for b in boundaries[1:]])}")
    print(f"  truth: {TRUTH.relative_to(lib.ROOT)}")
    print("  next: python3 tools/run_fixture_checks.py --end-to-end")


if __name__ == "__main__":
    main()
