#!/usr/bin/env python3
"""
read_video.py — open the finished export, record what it is, and stop.

    python3 stages/01_ingest/scripts/read_video.py <run-slug> <video>

WHY THIS IS ITS OWN STEP rather than three lines inside transcribe.py. The
duration and the frame rate are read once, here, and written down. Everything
downstream reads them from the file instead of probing the video again. That is
what keeps the caption timings, the render length and the trail describing the
same video — a second probe is a second chance for them to disagree.

It also fails early. A missing or unreadable file costs a millisecond here and
several minutes if transcription finds out first.

THIS TOOL TAKES ONE VIDEO, ALREADY CUT. You film in bursts, assemble in CapCut,
and export without captions. By the time the file reaches here the joins between
your clips are baked in and invisible, so nothing downstream knows or needs to
know that the take was filmed in pieces.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import pipeline_lib as lib  # noqa: E402

_FIELD = re.compile(r"^-\s+\*\*(.+?)\*\*\s*[—:]\s*(.+)$")


def read_record(run: Path) -> dict:
    """Parse 01-video.md back. It is a human edit surface, so it is the source
    of truth even if someone has changed a value by hand since."""
    path = lib.require(run / "01-video.md", "read_video.py")
    fields = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _FIELD.match(line.strip())
        if match:
            fields[match.group(1).strip().lower()] = match.group(2).strip().strip("`")

    missing = {"path", "duration", "frame rate"} - fields.keys()
    if missing:
        sys.exit(f"{path} is missing: {', '.join(sorted(missing))}. Re-run read_video.py.")

    return {
        "path": Path(fields["path"]),
        "duration": float(fields["duration"].split()[0]),
        "fps": float(fields["frame rate"].split()[0]),
    }


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: read_video.py <run-slug> <video>")
    slug, video = sys.argv[1], Path(sys.argv[2]).expanduser().resolve()
    run = lib.run_dir(slug, create=True)

    if not video.is_file():
        sys.exit(f"not a file: {video}")

    duration = lib.probe_duration(video)
    fps = lib.probe_frame_rate(video)

    print(f"  video       {video.name}")
    print(f"  duration    {lib.timecode(duration)}")
    print(f"  frame rate  {fps:.3f} fps")

    (run / "01-video.md").write_text("\n".join([
        f"# Source video — {slug}",
        "",
        "The finished export the captions will sit on. **This file is an edit",
        "surface**: correct a value here and re-run from `transcribe.py`.",
        "",
        f"- **Path** — `{video}`",
        f"- **Duration** — {duration:.3f} s",
        f"- **Frame rate** — {fps:.6f} fps",
        "",
        "The frame rate is kept to six decimal places on purpose. Phones and",
        "editors both produce 29.97, and rounding it to 30 drifts by one frame",
        "every thirty-three seconds — four frames late by the end of a two-minute",
        "take, which is where caption sync visibly goes wrong.",
        "",
    ]), encoding="utf-8")
    print(f"  wrote {lib.RUNS_REL}/{slug}/01-video.md")
    print("  next: transcribe.py")


if __name__ == "__main__":
    main()
