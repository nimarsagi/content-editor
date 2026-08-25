#!/usr/bin/env python3
"""
caption.py — the whole pipeline, end to end.

    python3 caption.py --topic "what this take is about"     the one video in input/
    python3 caption.py <your-capcut-export.mp4> --topic "..."
    python3 caption.py export.mp4 --topic "..." --slug pricing
    python3 caption.py --redo <slug>     after fixing a word in 01-transcript.json

ONE FINISHED VIDEO IN, ONE CAPTIONED VIDEO OUT. You cut in CapCut, export
without captions, and this transcribes it, chunks the words into cards, and
burns them on with Remotion.

THE ORDER MATTERS AND IS NOT NEGOTIABLE. The video must be cut BEFORE it gets
here. Transcribing raw clips and cutting afterwards produces word timings that
point at footage which no longer exists, and every caption drifts further out of
sync as the video goes on. Because this takes the finished export, the timings
and the pictures cannot disagree.

WHAT IT DOES NOT DO, on purpose: it proposes no cuts, removes no dead air, and
never decides where the video should start or end. The cutting is yours and
happens in CapCut. This tool captions what you hand it.

WHAT IT DOES LEARN: the words. Fix a misheard word in 01-transcript.json, and
`learn_words.py` notices. A word you have corrected in two separate runs gets
proposed for `_config/lexicon.txt`, which biases the next transcription so it
stops coming out wrong. Nothing is added without your yes.

--redo REBUILDS FROM THE TRANSCRIPT YOU CORRECTED. It skips reading the video
and skips transcribing — that is the point, because re-transcribing would
throw your correction away. Everything downstream of the words is rebuilt.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline_lib as lib  # noqa: E402

STEPS = [
    ("stages/01_ingest/scripts/read_video.py", "reading the video"),
    ("stages/01_ingest/scripts/transcribe.py", "transcribing"),
    ("stages/01b_calibrate/scripts/calibrate_audio.py", "levelling the audio"),
    ("stages/02_assemble/scripts/chunk_captions.py", "building caption cards"),
    ("stages/02_assemble/scripts/write_srt.py", "writing the .srt"),
    ("stages/03_render/scripts/render_captions.py", "burning captions on"),
]

# Where --redo picks up: everything that reads the transcript, nothing that
# writes it. The boundary is the whole safety of the feature, so it is derived
# from the step list rather than written out a second time and left to drift.
#
# MOVED FROM 2 TO 3 WHEN CALIBRATION WAS INSERTED, in the same change. Levelling
# needs the word timings, so it cannot sit above transcribe.py — and slotting it
# in below put it exactly where this boundary pointed, which would have made
# every --redo re-process a finished file. Correcting a word's spelling never
# changes the audio, so that work would produce an identical file at the cost of
# the slowest step in the chain. Calibration refuses its own output as a
# backstop; with the boundary here that refusal should never fire in normal use,
# and a safety rule that trips during ordinary work is one that gets switched off.
REDO_FROM = 3


VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v"}


def slugify(text: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in text]
    return "-".join(word for word in "".join(keep).split("-") if word)[:40]


def find_video(given: str | None) -> Path:
    """
    Find the video to caption, from most explicit to least:

        a path that exists          use it
        a bare name                 look for it in input/
        nothing at all              use the one video in input/

    The last form refuses to choose between two videos. Picking one silently
    would send you off to check a two-minute render of the wrong take.
    """
    inbox = lib.ROOT / "input"

    if given:
        direct = Path(given).expanduser()
        if direct.is_file():
            return direct.resolve()
        in_inbox = inbox / given
        if in_inbox.is_file():
            return in_inbox.resolve()
        sys.exit(f"no such video: {given}\n  Also looked in {inbox.name}/")

    found = sorted(p for p in inbox.glob("*")
                   if p.is_file() and p.suffix.lower() in VIDEO_SUFFIXES)
    if not found:
        sys.exit(f"no video given, and {inbox.name}/ is empty.\n"
                 f"  Drop your export in {inbox.name}/, or pass a path.")
    if len(found) > 1:
        listing = "\n".join(f"    {p.name}" for p in found)
        sys.exit(f"{len(found)} videos in {inbox.name}/ — name the one you mean:\n{listing}")
    return found[0].resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", nargs="?",
                        help="your finished CapCut export, captions not burned in. "
                             "A path, a name inside input/, or omitted entirely when "
                             "input/ holds exactly one video.")
    parser.add_argument("--topic",
                        help="one line: what this take is about. It seeds the "
                             "transcription and is kept with the run.")
    parser.add_argument("--slug", help="run name. Defaults to the date plus the topic.")
    parser.add_argument("--redo", metavar="SLUG",
                        help="rebuild an existing run's captions from its "
                             "01-transcript.json, which you have corrected by hand. "
                             "Does not re-transcribe.")
    args = parser.parse_args()

    if args.redo:
        if args.video or args.topic or args.slug:
            sys.exit("--redo takes a run slug and nothing else. It reuses that run's "
                     "video and topic; passing them again could only contradict it.")
        slug = args.redo
        run = lib.run_dir(slug)                       # exits if there is no such run
        lib.require(run / "01-transcript.json",
                    "transcribe.py — there is nothing to redo without it")
        video = None                                  # no step below step 2 opens it
        topic = (run / "01-topic.md").read_text(encoding="utf-8").strip()
        steps = list(enumerate(STEPS, start=1))[REDO_FROM:]
        print(f"\n  redo   {slug}   (from your corrected 01-transcript.json)")
        print(f"  topic  {topic}\n")
    else:
        if not args.topic:
            parser.error("--topic is required, unless you are using --redo.")

        video = find_video(args.video)

        topic = args.topic.strip()
        if not topic:
            sys.exit("--topic cannot be empty.")

        slug = args.slug or f"{date.today().isoformat()}-{slugify(topic)}"
        run = lib.run_dir(slug, create=True)
        (run / "01-topic.md").write_text(topic + "\n", encoding="utf-8")
        steps = list(enumerate(STEPS, start=1))

        print(f"\n  run    {slug}")
        print(f"  topic  {topic}")
        print(f"  video  {video}\n")

    for index, (script, label) in steps:
        print(f"\n--- {index}/{len(STEPS)}  {label} " + "-" * max(4, 44 - len(label)))
        cmd = [sys.executable, str(lib.ROOT / script), slug]
        if "read_video" in script:
            cmd.append(str(video))
        sys.stdout.flush()
        if subprocess.run(cmd).returncode != 0:
            sys.exit(f"\n  stopped at {Path(script).name}. The run does not continue.")

    print("\n" + "=" * 60)
    print(f"  Done. {lib.RUNS_REL}/{slug}/ has the whole trail — transcript, cards, .srt, props.")
    print("\n  If a word came out wrong:")
    print(f"    1. fix it in {lib.RUNS_REL}/{slug}/01-transcript.json")
    print(f"    2. python3 caption.py --redo {slug}")
    print(f"    3. python3 stages/04_learn/scripts/learn_words.py {slug}")
    print("       — that is what makes the fix stick for next time")
    print("=" * 60)


if __name__ == "__main__":
    main()
