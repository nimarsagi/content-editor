#!/usr/bin/env python3
"""
measure_audio.py — what the audio actually is, in numbers.

    python3 tools/measure_audio.py <run-slug>          the run's video, against its transcript
    python3 tools/measure_audio.py --noise <video>     background profile only, no transcript

WHY THIS EXISTS. The stated proof for audio calibration is "I can hear myself
whether it did a good job or not." That is the right final test and a useless
first one — it cannot tell you whether a change moved anything, or by how much,
or which of two settings is better. This prints the numbers so a change can be
checked instead of felt. Run it before a change and after.

It also answers the question the audio-calibration build rests on: how many
breaths sit in the silence between words (safe to treat) versus underneath
speech (not safe). On the first real export measured, the answer was 3 and 16 —
which retired two design choices before a line of the build was written.

READ THE BREATH COUNT WITH SUSPICION. A breath is detected here as: quiet
relative to speech, no pitch, noisy spectrum, 80-600ms long. Soft unvoiced
consonants — f, s, h, th — match all four. In dense speech most "under speech"
candidates are consonants, not breaths. That is not a flaw to fix; it is the
finding. Those signals cannot separate the two, and any breath tool built on
them inherits the problem.

THE GAP NUMBERS ARE THE TRUSTWORTHY ONES. They come from the word timings
alone, with no detector involved. If a clip has no silence longer than a
quarter second, nothing can sample its background — and that is a fact about
the recording, not about this script.

Needs numpy and ffmpeg. numpy is not in requirements.txt because nothing in the
pipeline proper uses it; this tool is the only thing that does.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pipeline_lib as lib  # noqa: E402

try:
    import numpy as np
except ImportError:
    sys.exit(
        "numpy is not installed, and this tool cannot run without it.\n"
        "  pip3 install numpy\n"
        "  Nothing else in the pipeline needs it — only this measurement tool."
    )

# CapCut's draft folder. This belongs in _config/paths.yaml once the audio build
# lands and something other than a measurement tool needs it. Left here for now
# rather than added to a config file this tool is the only reader of.
CAPCUT_DRAFTS = Path("~/Movies/CapCut/User Data/Projects/com.lveditor.draft").expanduser()

SR = 16000        # enough for speech and breath; breath energy sits around 1-4 kHz
FRAME = 400       # 25 ms
HOP = 160         # 10 ms
EPS = 1e-10
VOICED = 0.35     # autocorrelation peak above this counts as having pitch


# ------------------------------------------------------------------ audio

def decode(video: Path) -> np.ndarray:
    """Mono float samples, via ffmpeg. Nothing is written to disk."""
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video),
         "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        capture_output=True,
    )
    if result.returncode != 0:
        sys.exit(f"could not read audio from {video.name}:\n{result.stderr.decode().strip()}")
    return np.frombuffer(result.stdout, dtype=np.float32)


def features(x: np.ndarray):
    """Per-frame level, spectral flatness, and a voicing estimate.

    Flatness separates a noisy sound (breath, hiss, s) from a harmonic one (a
    vowel). Voicing separates anything with a pitch from anything without. Level
    alone is not enough for either — a quiet vowel and a loud breath overlap.
    """
    count = 1 + (len(x) - FRAME) // HOP
    index = np.arange(FRAME)[None, :] + HOP * np.arange(count)[:, None]
    frames = x[index]

    db = 20 * np.log10(np.sqrt(np.mean(frames ** 2, axis=1)) + EPS)

    windowed = frames * np.hanning(FRAME)[None, :]
    spectrum = np.abs(np.fft.rfft(windowed, axis=1)) ** 2 + EPS
    flatness = np.exp(np.mean(np.log(spectrum), axis=1)) / np.mean(spectrum, axis=1)

    # Voicing by normalised autocorrelation over the 60-400 Hz lag range. A
    # pitched frame correlates strongly with itself one pitch period later; a
    # breath does not correlate with itself at any lag.
    centred = frames - frames.mean(axis=1, keepdims=True)
    energy = np.sum(centred ** 2, axis=1) + EPS
    voiced = np.zeros(count)
    for lag in range(SR // 400, SR // 60):
        c = np.sum(centred[:, lag:] * centred[:, :-lag], axis=1) / energy
        voiced = np.maximum(voiced, c)

    return np.arange(count) * HOP / SR, db, flatness, voiced


def runs_of(mask: np.ndarray, t: np.ndarray, lo: float, hi: float):
    """Contiguous true stretches lasting between lo and hi seconds."""
    out, start = [], None
    for i, on in enumerate(mask):
        if on and start is None:
            start = i
        elif not on and start is not None:
            if lo <= t[i] - t[start] <= hi:
                out.append((t[start], t[i]))
            start = None
    if start is not None and lo <= t[-1] - t[start] <= hi:
        out.append((t[start], t[-1]))
    return out


# ------------------------------------------------------------------ CapCut

def find_project(duration: float, tolerance: float = 0.10):
    """The CapCut project whose timeline is as long as this export.

    THE MATCH IS ON DURATION AND NOTHING ELSE, because nothing else is reliable:
    the draft folder is named by the person, the export is named by CapCut, and
    neither carries the other's name. Timeline length is exact — on the machine
    this was written against, three drafts measured 119.63s, 81.53s and 55.60s
    against an export of 55.600000s.

    A near-miss is not a match. If the project has been edited since the export,
    the boundaries it reports would be wrong, and silently wrong is the whole
    danger — so this returns nothing rather than the closest one.
    """
    if not CAPCUT_DRAFTS.is_dir():
        return None, []
    seen = []
    for info in sorted(CAPCUT_DRAFTS.glob("*/draft_info.json")):
        try:
            project = json.loads(info.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        length = project.get("duration", 0) / 1e6
        seen.append((info.parent.name, length))
        if abs(length - duration) <= tolerance:
            return info, seen
    return None, seen


def clips(info: Path):
    """Timeline clip boundaries, in seconds, plus any hand-set gain."""
    project = json.loads(info.read_text(encoding="utf-8"))
    out = []
    for track in project.get("tracks", []):
        if track.get("type") != "video":
            continue
        for segment in track.get("segments", []):
            span = segment["target_timerange"]
            out.append((span["start"] / 1e6,
                        (span["start"] + span["duration"]) / 1e6,
                        segment.get("volume", 1.0)))
    return sorted(out)


# ------------------------------------------------------------------ report

def background(x: np.ndarray, db: np.ndarray, label: str) -> None:
    """What the background sounds like, and whether it is steady.

    The shape matters more than the level. A flat low hum and a broadband hiss
    can sit at the same number and behave completely differently: one is nearly
    free to filter out, the other is not, and neither can stand in for the
    other as room tone.
    """
    quiet = db < np.percentile(db, 20)
    count = 1 + (len(x) - FRAME) // HOP
    index = np.arange(FRAME)[None, :] + HOP * np.arange(count)[:, None]
    windowed = x[index][quiet] * np.hanning(FRAME)[None, :]
    spectrum = np.abs(np.fft.rfft(windowed, axis=1)) ** 2 + EPS
    freqs = np.fft.rfftfreq(FRAME, 1 / SR)
    mean = spectrum.mean(axis=0)

    print(f"\n  --- {label} ---")
    print(f"  level        {np.percentile(db, 5):6.1f} dBFS")
    print(f"  steadiness   ±{np.std(db[quiet]):5.1f} dB   "
          f"(low = a steady hum, high = it moves around)")
    print("  energy by frequency:")
    for lo, hi in [(0, 300), (300, 1000), (1000, 3000), (3000, 8000)]:
        band = (freqs >= lo) & (freqs < hi)
        share = 100 * mean[band].sum() / mean.sum()
        bar = "#" * int(share / 2)
        print(f"    {lo:5d}-{hi:5d} Hz  {share:5.1f}%  {bar}")
    print("  Breath lives around 1000-4000 Hz. Background that is quiet there")
    print("  does not hide breaths. Background that is loud there does.")


def measure(video: Path, transcript: dict | None) -> None:
    x = decode(video)
    duration = len(x) / SR
    t, db, flatness, voiced = features(x)
    peak = 20 * np.log10(np.max(np.abs(x)) + EPS)

    print(f"\n  {video.name}   {lib.timecode(duration)}")
    print(f"  peak         {peak:6.1f} dBFS   ({abs(peak):.1f} dB below clipping)")

    if transcript is None:
        background(x, db, "background")
        return

    words = [(w["start"], w["end"]) for w in transcript["words"]]
    in_word = np.zeros(len(t), dtype=bool)
    for a, b in words:
        in_word |= (t >= a) & (t < b)

    speech = np.median(db[in_word & (voiced > VOICED)])
    floor = np.percentile(db, 5)
    print(f"  speech       {speech:6.1f} dBFS   (median voiced frame)")
    print(f"  background   {floor:6.1f} dBFS")
    print(f"  separation   {speech - floor:6.1f} dB")
    print(f"  words        {len(words)} in {duration:.1f}s")

    # ---- gaps. No detector involved — this is the word timings and nothing else.
    gaps = runs_of(~in_word, t, 0.0, 1e9)
    lengths = np.array([b - a for a, b in gaps]) if gaps else np.array([0.0])
    print(f"\n  --- silence between words ---")
    print(f"  {len(gaps)} gaps, {lengths.sum():.1f}s total "
          f"({100 * lengths.sum() / duration:.0f}% of the video)")
    print(f"  longest {lengths.max():.2f}s   median {np.median(lengths):.2f}s   "
          f"{(lengths >= 0.30).sum()} are 300ms or longer")

    # ---- breath candidates
    candidate = (
        (db < speech - 8) & (db > floor + 4)
        & (voiced < VOICED)
        & (flatness > np.percentile(flatness, 60))
    )
    breaths = runs_of(candidate, t, 0.08, 0.60)
    silent, straddle, under = [], [], []
    for a, b in breaths:
        share = in_word[(t >= a) & (t < b)].mean()
        (under if share > 0.7 else silent if share < 0.3 else straddle).append((a, b))

    print(f"\n  --- breath candidates ---")
    print(f"  {len(breaths)} found (80-600ms, quiet, no pitch, noisy)")
    print(f"    {len(silent):3d}  in silence between words   <- safe to treat fully")
    print(f"    {len(straddle):3d}  straddling a word edge")
    print(f"    {len(under):3d}  underneath speech          <- cannot be told from f/s/h/th")

    background(x, db, "background")

    # ---- per clip, if the CapCut project can be matched
    info, seen = find_project(duration)
    if info is None:
        print(f"\n  --- clips ---")
        print(f"  no CapCut project matches {duration:.2f}s, so no clip boundaries.")
        for name, length in seen:
            print(f"    {name:12} timeline {length:7.2f}s")
        print("  A near miss is not used on purpose: if the project was edited")
        print("  after the export, its boundaries would be silently wrong.")
        return

    print(f"\n  --- clips (from CapCut project {info.parent.name}) ---")
    levels = []
    for a, b, gain in clips(info):
        selected = (t >= a) & (t < b) & in_word & (voiced > VOICED)
        if selected.sum() < 5:
            continue
        level = np.median(db[selected])
        clip_peak = 20 * np.log10(np.max(np.abs(x[int(a * SR):int(b * SR)])) + EPS)
        # Gaps trimmed to this clip's span, not only gaps wholly inside it — a
        # gap straddling a cut still gives this clip somewhere to sample from.
        inner = [min(gb, b) - max(ga, a) for ga, gb in gaps
                 if gb > a and ga < b]
        levels.append(level)
        print(f"    {a:6.2f}-{b:6.2f}s  speech {level:6.1f} dB  peak {clip_peak:6.1f} dB"
              f"  gain {gain:.3f}  longest gap {max(inner) if inner else 0:.2f}s")

    if levels:
        print(f"\n  spread between quietest and loudest clip: "
              f"{max(levels) - min(levels):.1f} dB")
        print("  A clip with no gap over ~0.30s has nowhere to sample its own")
        print("  background from. That is what rules out per-clip room tone.")


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__.strip().splitlines()[2].strip())

    if args[0] == "--noise":
        if len(args) < 2:
            sys.exit("usage: measure_audio.py --noise <video>")
        video = Path(args[1]).expanduser()
        if not video.is_file():
            sys.exit(f"not a file: {video}")
        measure(video.resolve(), None)
        return

    slug = args[0]
    run = lib.run_dir(slug)
    transcript = lib.read_json(lib.require(run / "01-transcript.json", "transcribe.py"))
    video = Path(transcript["video"])
    if not video.exists():
        sys.exit(f"the video this run was built from has moved:\n    {video}")
    measure(video, transcript)


if __name__ == "__main__":
    main()
