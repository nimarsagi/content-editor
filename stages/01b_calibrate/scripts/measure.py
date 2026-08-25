#!/usr/bin/env python3
"""
measure.py — how loud the speech is, per stretch of the video.

    python3 stages/01b_calibrate/scripts/measure.py <run-slug>

A library first, a command second. segment.py and apply_gain.py import it; run
directly it prints what it measured, which is how the numbers get checked
against ears.

LEVELS ARE MEASURED ON SPEECH AND NOTHING ELSE. 10-11% of this person's videos
is silence between words, and the share differs per clip, so measuring across a
whole stretch reads the clips with more pauses in them as quieter than they are.
A frame counts only if it falls inside a word AND has a pitch to it — the word
timings come from the transcript, the pitch test throws out the unvoiced
consonants inside a word, which carry no level worth matching.

IT DOES NOT DUPLICATE tools/measure_audio.py. That tool already decodes to mono
16 kHz, frames at 25ms/10ms and derives level and voicing with numpy alone, and
the numbers in the measurement record were produced by it. Measuring the same
thing a second way here would let the build and its own evidence drift apart, so
this imports it and adds only what it lacks: the high-pass, and levels per span
rather than per file.

THE HIGH-PASS IS APPLIED BEFORE ANYTHING IS MEASURED. Nothing in speech lives
below 80 Hz and the background energy of these recordings is concentrated down
there, so a level measured with the rumble still in it describes the room as
much as the voice. Same corner as the delivered file gets, so the measurement
describes the file that is actually written.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import pipeline_lib as lib  # noqa: E402
import measure_audio as ma  # noqa: E402  — the measurement this build is evidenced by

try:
    import numpy as np
except ImportError:
    sys.exit(
        "numpy is not installed, and calibration cannot run without it.\n"
        "  pip3 install -r requirements.txt"
    )

# Below this many voiced frames a median is not a measurement, it is an opinion.
# Not config: it is a property of taking a median, not a value to tune.
MIN_FRAMES = 5


def settings() -> dict:
    """The audio rules, with any override from memory/preferences.md applied."""
    rules = lib.rules()
    if "audio" not in rules:
        sys.exit(
            "_config/edit-defaults.yaml has no `audio:` block under `rules:`.\n"
            "  Calibration reads every threshold from there and holds none of\n"
            "  its own. Restore the block before running."
        )
    preferences = lib.load_preferences("Audio")
    lib.apply_overrides(rules, preferences["overrides"])
    return rules["audio"]


def unknown_keys(overrides: dict, audio: dict) -> list[str]:
    """
    Audio rules in preferences.md that name nothing in config.

    The conviction behind this build is "if I say that I want the audio to be
    adjusted, then the program should do as I say", and preferences.md warns
    that anything not mechanical is "prose for you, not for the script". So a
    mistyped key does nothing — and the failure this must not have is the silent
    one. Reported, never fatal: a typo is a typo, not a corrupted run.
    """
    return [key for key in overrides
            if not key.startswith("audio.") or key.split(".", 1)[1] not in audio]


def load(video: Path, highpass_hz: float) -> np.ndarray:
    """Mono float samples at the measurement rate, rumble already removed."""
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video),
         "-af", f"highpass=f={highpass_hz}",
         "-ac", "1", "-ar", str(ma.SR), "-f", "f32le", "-"],
        capture_output=True,
    )
    if result.returncode != 0:
        sys.exit(f"could not read audio from {video.name}:\n"
                 f"{result.stderr.decode().strip()}")
    return np.frombuffer(result.stdout, dtype=np.float32)


def speech_frames(x: np.ndarray, words: list[dict]):
    """
    Per-frame time and level, plus the mask of frames that are actually speech.

    Returns (t, db, is_speech). Everything downstream measures through the mask,
    so no caller has to remember the rule.
    """
    t, db, _flatness, voiced = ma.features(x)
    in_word = np.zeros(len(t), dtype=bool)
    for word in words:
        in_word |= (t >= word["start"]) & (t < word["end"])
    return t, db, in_word & (voiced > ma.VOICED)


def level(db: np.ndarray, is_speech: np.ndarray, start: float, end: float,
          t: np.ndarray) -> float | None:
    """
    Median speech level across one span, in dBFS, or None if there is too little
    speech in it to measure.

    Median rather than mean: one loud syllable should not move a clip's level,
    and the frame-to-frame spread inside a clip is 6.9 dB, which a mean would
    chase.
    """
    selected = is_speech & (t >= start) & (t < end)
    if selected.sum() < MIN_FRAMES:
        return None
    return float(np.median(db[selected]))


def step_across(db: np.ndarray, is_speech: np.ndarray, t: np.ndarray,
                position: float, window: float) -> float | None:
    """
    How far the speech level jumps across one position — measured `window`
    seconds either side of it, not between the averages of the clips that meet
    there. None when either side holds too little speech to measure.

    THIS IS THE MEASUREMENT THE FIRST BUILD GOT WRONG, and the fault was
    audible. It compared the average of the whole segment before against the
    whole segment after. A cut is a discontinuity, and averaging a whole clip
    is the one operation guaranteed to hide one: the clip starting at 44.58s on
    the reel opens at -20.1 dB and ends near -29, so its average of -25.06 sits
    within 1 dB of its neighbour's -24.07. The join read as flat because the
    clip's own fall cancelled its loud opening. The boundary was discarded,
    22.7 seconds spanning three clips became one segment, and the report was
    "the clip at 00:46 is a lot louder than the clip before".

    IT DOES NOT MOVE WHEN A NEIGHBOURING SEGMENT IS MERGED. The two spans are
    fixed either side of the position, so this reads the same before and after
    any merge — unlike a whole-segment average, which changes every time the
    segments do. That is what stops one discarded boundary from cascading into
    the next, which is how the boundary at 38.78s was lost.
    """
    before = level(db, is_speech, position - window, position, t)
    after = level(db, is_speech, position, position + window, t)
    if before is None or after is None:
        return None
    return abs(after - before)


def second_by_second(db: np.ndarray, is_speech: np.ndarray, t: np.ndarray,
                     window_s: float, shift: np.ndarray | None = None) -> list[float]:
    """
    The speech level in each `window_s` window of the video, in dBFS.

    THIS IS THE CURVE THE EAR FOLLOWS, AND IT IS NOT WHAT THE FIRST BUILD
    REPORTED. That headline — a spread of 7.23 dB closing to 1.81 — was the
    spread of the SEGMENT AVERAGES, which is the quantity the corrections are
    computed from and therefore the one they are guaranteed to improve. It was
    true, and it was blind to exactly what was heard. Reported alongside the
    old figure rather than instead of it, labelled, so the two cannot be read
    for each other again.

    `shift` is a per-frame gain in dB, which is what lets a correction be
    measured before it is applied to anything.
    """
    values = db if shift is None else db + shift
    levels = []
    start = 0.0
    while start < float(t[-1]):
        selected = is_speech & (t >= start) & (t < start + window_s)
        if selected.sum() >= MIN_FRAMES:
            levels.append(float(np.median(values[selected])))
        start += window_s
    return levels


def steadiness(curve: list[float]) -> tuple[float, float]:
    """
    How much a level curve moves: the typical distance from its own average,
    and the band the middle 80% of it sits in. Both in dB, both smaller is
    steadier.

    NOT max-minus-min. One held shout at the end of one take would decide the
    number, and the question here is what the whole video sounds like.
    """
    if len(curve) < 2:
        return 0.0, 0.0
    return (float(np.std(curve)),
            float(np.percentile(curve, 90) - np.percentile(curve, 10)))


def voiced_seconds(is_speech: np.ndarray, start: float, end: float,
                   t: np.ndarray) -> float:
    """How much actual speech a span holds — not its wall-clock length."""
    selected = is_speech & (t >= start) & (t < end)
    return float(selected.sum() * ma.HOP / ma.SR)


def reference(levels: list[float]) -> float:
    """
    The level everything is corrected toward: the mean of the per-segment
    decibel values.

    IN DECIBELS, NOT IN LINEAR ENERGY, and the difference is the point. Averaging
    energy lets one loud clip dominate the reference and drags every quiet clip
    up toward it. Averaging the decibel values treats each clip as one vote.

    THERE IS NO CONFIGURED TARGET, on purpose — "I have no target value". The
    reference is computed from the run's own clips every time, which is also the
    only form that survives the finding that no absolute threshold holds across
    two of this person's videos.
    """
    return float(np.mean(levels))


def spread(levels: list[float]) -> float:
    """Quietest to loudest, in dB. The number the build exists to shrink."""
    return float(max(levels) - min(levels)) if levels else 0.0


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: measure.py <run-slug>")
    slug = sys.argv[1]
    run = lib.run_dir(slug)

    sys.path.insert(0, str(lib.ROOT / "stages" / "01_ingest" / "scripts"))
    from read_video import read_record  # noqa: E402

    audio = settings()
    record = read_record(run)
    video = record["path"]
    if not video.exists():
        sys.exit(f"the video has moved or been deleted:\n    {video}")

    transcript = lib.read_json(lib.require(run / "01-transcript.json", "transcribe.py"))
    words = transcript["words"]
    if not words:
        sys.exit("the transcript has no words in it — nothing to measure speech against.")

    x = load(video, audio["highpass_hz"])
    t, db, is_speech = speech_frames(x, words)

    whole = level(db, is_speech, 0.0, record["duration"], t)
    peak = 20 * np.log10(np.max(np.abs(x)) + ma.EPS)
    print(f"\n  {video.name}   {lib.timecode(record['duration'])}")
    print(f"  high-pass    {audio['highpass_hz']} Hz, applied before measuring")
    print(f"  speech       {whole:6.1f} dBFS   (median voiced frame, whole file)")
    print(f"  peak         {peak:6.1f} dBFS")
    print(f"  speech is    {100 * is_speech.mean():.0f}% of frames")


if __name__ == "__main__":
    main()
