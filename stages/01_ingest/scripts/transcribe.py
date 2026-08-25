#!/usr/bin/env python3
"""
transcribe.py — the finished video, one timestamp per word.

Word-level timestamps are non-negotiable. They are what makes splitting captions
on breath and clause boundaries possible at all, and a build that quietly
downgrades to sentence-level timing looks correct here and ruins the chunking.

Local model, no account, no subscription — replacing a paywalled subtitle
generator is why this build exists.

TWO FILES COME OUT AND THAT IS THE POINT:

  01-transcript.json      yours. Fix a misheard word here and re-run.
  01-transcript-raw.json  the machine's, never touched by anyone.

The second one is not a backup. It is the only record of what the model
originally heard, and `learn_words.py` compares the two to find the words you
corrected. Without it, a fix is invisible the moment you make it and the tool
can never learn the word.

    python3 stages/01_ingest/scripts/transcribe.py <run-slug>
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline_lib as lib  # noqa: E402
from read_video import read_record  # noqa: E402

MODEL_SIZE = "medium"      # accuracy/speed trade-off on CPU. "small" if too slow.
COMPUTE_TYPE = "int8"      # what makes this viable without a GPU


def build_prompt(topic: str, terms: list[str]) -> str | None:
    """
    Bias the model toward the words that carry the meaning.

    Speech-to-text reliably mangles proper nouns, brand names and acronyms, which
    in this subject matter are exactly the load-bearing words. The topic goes in
    alongside them because it costs nothing and steers the same way.
    """
    parts = []
    if topic:
        parts.append(f"This recording is about {topic}.")
    if terms:
        parts.append("Terms used in it: " + ", ".join(terms) + ".")
    return " ".join(parts) or None


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: transcribe.py <run-slug>")
    slug = sys.argv[1]
    run = lib.run_dir(slug)

    # --- the topic gate, FIRST ------------------------------------------
    # Transcription is the slow step. Failing after it wastes minutes for a
    # condition we can check in a millisecond.
    topic_file = run / "01-topic.md"
    if not topic_file.exists() or not topic_file.read_text(encoding="utf-8").strip():
        sys.exit(
            "no topic stated for this run.\n"
            f"  Write one line into {topic_file.relative_to(lib.ROOT)} and run again.\n"
            "  It seeds the transcription — the model gets it as context and mangles\n"
            "  fewer of the words that carry the meaning — and it is how you will\n"
            "  recognise this run in six months."
        )
    topic = topic_file.read_text(encoding="utf-8").strip()
    print(f"  topic       {topic}")

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit(
            "faster-whisper is not installed.\n"
            "  pip3 install -r requirements.txt"
        )

    terms = lib.load_lexicon()
    prompt = build_prompt(topic, terms)
    print(f"  lexicon     {len(terms)} terms seeding transcription")

    # The path and the duration come from 01-video.md, which read_video.py wrote
    # and the person may since have hand-edited. That file is the source of
    # truth — probing the video again here would let the two disagree.
    record = read_record(run)
    video = record["path"]
    if not video.exists():
        sys.exit(f"the video has moved or been deleted:\n    {video}")

    print(f"  loading whisper '{MODEL_SIZE}' ({COMPUTE_TYPE}) — first run downloads it")
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type=COMPUTE_TYPE)

    print(f"  transcribing {video.name}  {lib.timecode(record['duration'])}", flush=True)
    segments, _info = model.transcribe(
        str(video),
        word_timestamps=True,          # NON-NEGOTIABLE
        initial_prompt=prompt,
        vad_filter=False,              # the video is already cut; nothing here
                                       # removes silence, so filtering it out of
                                       # the audio would only shift timings
    )

    words: list[dict] = []
    for segment in segments:
        if not segment.words:
            sys.exit(
                f"{video.name} came back with segment-level timing only.\n"
                "  Word-level timestamps are a hard requirement — captions cannot be\n"
                "  split on breath boundaries without them."
            )
        for word in segment.words:
            words.append({
                "word": word.word.strip(),
                "start": round(word.start, 3),
                "end": round(word.end, 3),
                "probability": round(word.probability, 3),
            })

    if not words:
        sys.exit(f"nothing was transcribed from {video.name}. Is there audio on it?")

    transcript = {
        "topic": topic,
        "video": str(video),
        "duration": record["duration"],
        "fps": record["fps"],
        "words": words,
    }
    lib.write_json(run / "01-transcript.json", transcript)

    # The untouched copy, written once and never again. `learn_words.py` reads it
    # to tell your corrections apart from what the model actually said.
    raw_path = run / "01-transcript-raw.json"
    if raw_path.exists():
        # A re-run would otherwise overwrite the original with an already-corrected
        # version, and every fix made so far would stop being visible as a fix.
        print(f"  ! {raw_path.name} already exists — left alone, it is the original")
    else:
        shutil.copyfile(run / "01-transcript.json", raw_path)
        print(f"  wrote {lib.RUNS_REL}/{slug}/01-transcript-raw.json  (the original, never edit it)")

    low = [w for w in words if w["probability"] < 0.5]
    print(f"\n  {len(words)} words across {lib.timecode(record['duration'])}")
    if low:
        print(f"  {len(low)} words the model was unsure of — likely the ones to check:")
        for word in low[:8]:
            print(f"    {lib.timecode(word['start'])}  {word['word']!r}  "
                  f"{word['probability']:.0%}")
    print("  next: chunk_captions.py")


if __name__ == "__main__":
    main()
