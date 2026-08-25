#!/usr/bin/env python3
"""
apply_gain.py — the corrections, the ceiling, and the checks that stop the run.

Imported by calibrate_audio.py. Not run on its own — segment.py is the dry run.

THREE OPERATIONS, IN THIS ORDER, AND THE ORDER IS LOAD-BEARING.

  1. Flatten the drift INSIDE each segment, around that segment's own mean.
  2. Move each segment toward the run's average level.
  3. Cap the peaks.

One and two cannot swap. Correcting drift changes a segment's average unless it
is done around that average, so applying the offset first would leave the drift
step moving every clip against the reference just measured. Mean-preserving is
what keeps the two from fighting.

THE CEILING IS NEVER ENFORCED BY TURNING A CLIP DOWN. Lowering whole-clip gain
until the loudest consonant clears the meter makes the clip quiet and lands every
clip at a different level, which is the problem this stage exists to solve. The
limiter reduces gain across the peak itself and lets go again.

GAIN ONLY EVER CHANGES AT A WORD BOUNDARY, AND IT RAMPS. A level change in the
middle of a word is audible; the same change in the gap before it is not. No gain
ever moves while a word is playing.

HOW MUCH IT MOVES BETWEEN WORDS IS THE THING TO LISTEN FOR. The straight-line
version this replaced moved about 2.5 dB between neighbouring words at the 95th
percentile; following the level over a 1.5-second window moves about 3.4 dB. The
level it follows is still measured over more than a second, so it tracks the
voice rather than the syllable — but it is nearer that edge than what came
before, and `drift_window_s` is the value to raise if a finished video sounds
worked-on. The standing constraint is the person's own — "without sacrificing
the coherence/consistency of the audio" — which is a test applied by listening.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline_lib as lib  # noqa: E402
import measure as mm  # noqa: E402

import numpy as np  # noqa: E402


def decode_full(video: Path, rate: int, channels: int, highpass_hz: float,
                expect_samples: int | None = None) -> np.ndarray:
    """
    The audio at its own rate and channel count, rumble removed, shape (n, ch).

    NOT DOWNMIXED. The source is a mono recording carried in a stereo container —
    the two channels measured bit-identical across 2,452,416 frames — so averaging
    them would be a no-op today and a quiet loss the day it stops being true. One
    gain envelope is computed and applied to every channel, which gives what
    "process one channel and copy it to both" was protecting: the channels cannot
    drift apart, because there is only ever one envelope.

    TRIMMED TO THE LENGTH THE CONTAINER DECLARES, and that is not cosmetic. An
    AAC decoder emits whole 1024-sample frames, so the last frame is padded and
    the decode comes back LONGER than the audio really is — 472,064 samples
    against a declared 469,366 on the test fixture, 61 ms of invented tail.
    Writing that out would make the file a different length from the one that
    went in, which is the thing the length check exists to catch.

    THE PADDING IS ALL AT THE END, VERIFIED RATHER THAN ASSUMED. A click written
    at a known sample, encoded to AAC and decoded back, returns at exactly that
    sample — start offset zero. So trimming the tail is safe and trimming the
    head would be wrong.
    """
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video),
         "-af", f"highpass=f={highpass_hz}",
         "-ar", str(rate), "-ac", str(channels), "-f", "f32le", "-"],
        capture_output=True,
    )
    if result.returncode != 0:
        sys.exit(f"could not read audio from {video.name}:\n"
                 f"{result.stderr.decode().strip()}")
    flat = np.frombuffer(result.stdout, dtype=np.float32).astype(np.float64)
    audio = flat.reshape(-1, channels)

    if expect_samples and len(audio) > expect_samples:
        audio = audio[:expect_samples]
    elif expect_samples and len(audio) < expect_samples:
        sys.exit(
            f"the decoder returned less audio than {video.name} declares:\n"
            f"  {len(audio)} samples against {expect_samples}.\n"
            "  Padding it would be inventing audio. The run stops here.")
    return audio


def flatten(words, indices, db, is_speech, t, span, correction, window_s,
            min_fit_s) -> dict[int, float]:
    """
    How much to move each word so the level holds steady across one segment.

    For every word: measure the speech level over `window_s` seconds of audio
    AROUND IT, and move that word by however far it sits from the segment's own
    average. Returns a shift per word index; words it cannot measure are absent.

    MEASURED OVER TIME, NOT PER WORD, AND THAT DISTINCTION IS THE WHOLE FUNCTION.
    A word's own median level is close to worthless: 26 of 216 words on the reel
    have fewer than five voiced frames, and inside two seconds the per-word
    figures run from -11.4 dB on "this" to -51.7 dB on "is". That is not the
    voice changing by 40 dB, it is short function words being measured from
    almost nothing. Averaging over a window of AUDIO weights each word by how
    long it actually sounds, so a clipped "is" contributes what it is worth.

    WHAT IT REPLACED, AND WHY. This was a straight line fitted to the per-word
    levels. A line can only remove a tilt, and the levels inside a clip do not
    tilt — they hump. After the boundary fix the reel still had eleven seconds
    sitting more than 3 dB off its own average and four more than 5 dB, which
    was reported as "some parts are significantly louder than others". The
    per-word noise above is also why smoothing the word levels instead barely
    helped: the noise survives the smoothing.

        on the reel          seconds >3 dB off   >5 dB   worst second
        straight line               11             4        6.26 dB
        this, at 1.5s                2             0        4.15 dB

    THE WINDOW IS CLAMPED TO THE SEGMENT. A word near a join must not average in
    the clip on the other side of it — that would quietly undo the boundary work
    by dragging both sides toward each other.

    MEAN-PRESERVING BY CONSTRUCTION: what is subtracted is each local level minus
    their average over the segment, so the average correction across the segment
    is zero and the between-segment offset still means what it measured.

    SKIPPED ON A SEGMENT WITH TOO LITTLE SPEECH. Reading a level curve off a
    second of speech reads noise as shape, and a wrong shape is worse than none.
    """
    if len(indices) < 3:
        return {}
    start, end = span
    centres = {i: (words[i]["start"] + words[i]["end"]) / 2 for i in indices}
    if max(centres.values()) - min(centres.values()) < min_fit_s:
        return {}

    local = {}
    for i, centre in centres.items():
        a = max(centre - window_s / 2, start)
        b = min(centre + window_s / 2, end)
        selected = is_speech & (t >= a) & (t < b)
        if selected.sum() >= mm.MIN_FRAMES:
            local[i] = float(np.median(db[selected]))
    if len(local) < 3:
        return {}

    average = float(np.mean(list(local.values())))
    return {i: -correction * (level - average) for i, level in local.items()}


def envelope(words, gains_db, total_samples, rate, ramp_ms) -> np.ndarray:
    """
    A gain in dB for every sample: flat under each word, ramping between them.

    The ramp is capped by the gap it has to cross, so a change never bleeds into
    the word on either side. The gaps are ample for this — median 0.24s and 0.15s
    on the two measured videos, against a ramp measured in tens of milliseconds.
    """
    curve = np.empty(total_samples)
    ramp = ramp_ms / 1000.0

    edges = []
    for word, gain in zip(words, gains_db):
        edges.append((word["start"], word["end"], gain))

    # Before the first word and after the last, hold the nearest word's gain —
    # there is no speech out there to protect, and a jump at the very edge of the
    # file is still a jump.
    curve[:] = edges[0][2]
    for index, (start, end, gain) in enumerate(edges):
        a = int(start * rate)
        b = min(int(end * rate), total_samples)
        curve[a:b] = gain

        if index + 1 < len(edges):
            next_start, _, next_gain = edges[index + 1]
            gap = max(next_start - end, 0.0)
            if gap <= 0:
                # Words touching: no room to ramp, so the change lands on the
                # boundary itself. Still not mid-word.
                continue
            span = min(ramp, gap)
            centre = (end + next_start) / 2
            r0 = int(max(centre - span / 2, end) * rate)
            r1 = int(min(centre + span / 2, next_start) * rate)
            curve[b:r0] = gain
            if r1 > r0:
                curve[r0:r1] = np.linspace(gain, next_gain, r1 - r0)
            curve[r1:int(next_start * rate)] = next_gain
        else:
            curve[b:] = gain

    return curve


# ------------------------------------------------------------------ limiter

def _oversample_kernel(factor: int, taps: int = 33) -> np.ndarray:
    """A windowed-sinc interpolator, the standard way true peak is estimated."""
    n = np.arange(taps * factor) - (taps * factor - 1) / 2
    kernel = np.sinc(n / factor) * np.hanning(taps * factor)
    return kernel / kernel.sum() * 1.0


def true_peak(x: np.ndarray, factor: int = 4) -> np.ndarray:
    """
    The signal as a converter would reconstruct it, at `factor` times the rate.

    A sample peak under the ceiling can still reconstruct above it — the wave
    between two samples goes higher than either. Measuring the samples alone is
    what lets a file that "does not clip" clip on playback.
    """
    kernel = _oversample_kernel(factor)
    stuffed = np.zeros(len(x) * factor)
    stuffed[::factor] = x
    return np.convolve(stuffed, kernel, mode="same") * factor


def limit(audio: np.ndarray, ceiling_dbtp: float, rate: int,
          lookahead_ms: float, release_ms: float) -> tuple[np.ndarray, float]:
    """
    Hold the true peak under the ceiling, reducing gain only across each peak.

    Returns the limited audio and the share of it the limiter touched — which is
    worth printing, because a limiter working hard means the levelling pushed
    something too hot.

    LOOKAHEAD IS WHAT MAKES IT INAUDIBLE. Without it the reduction starts on the
    peak and the attack itself is a click. The envelope is pulled earlier by the
    lookahead and taken as a running minimum, so the gain is already down by the
    time the peak arrives.

    RELEASE IS WHAT DECIDES WHETHER IT PUMPS. The standing constraint is the
    person's own — "without sacrificing the coherence/consistency of the audio" —
    which is a test applied by listening, not a technique ruled out in advance.
    So this is a value to set by ear, not to inherit.
    """
    ceiling = 10 ** (ceiling_dbtp / 20)
    peak = np.max(np.abs(np.stack([true_peak(audio[:, c])
                                   for c in range(audio.shape[1])])), axis=0)
    # Back to the sample grid: the worst reconstructed value near each sample.
    factor = len(peak) // len(audio)
    per_sample = peak[:len(audio) * factor].reshape(-1, factor).max(axis=1)

    over = per_sample > ceiling
    if not over.any():
        return audio, 0.0

    reduction = np.ones(len(audio))
    reduction[over] = ceiling / per_sample[over]

    # Lookahead: a running minimum over the window before each sample.
    window = max(int(lookahead_ms / 1000 * rate), 1)
    padded = np.concatenate([reduction, np.ones(window)])
    strided = np.lib.stride_tricks.sliding_window_view(padded, window + 1)
    reduction = strided.min(axis=1)[:len(audio)]

    # Release: a one-pole rise back to unity, so it lets go over milliseconds
    # rather than instantly.
    coefficient = np.exp(-1.0 / (release_ms / 1000 * rate))
    smoothed = np.empty_like(reduction)
    running = 1.0
    for i, value in enumerate(reduction):
        running = value if value < running else value + (running - value) * coefficient
        smoothed[i] = running

    return audio * smoothed[:, None], float(over.mean())


# ------------------------------------------------------------------- output

def write(audio: np.ndarray, source: Path, destination: Path, rate: int) -> None:
    """
    Mux the new audio onto the untouched picture.

    THE PICTURE IS COPIED, NEVER RE-ENCODED. The export arrives as HEVC and the
    caption renderer re-encodes at its own later stage; adding a generation of
    loss in between would be paid for twice and seen once.

    THE AUDIO IS WRITTEN AS PCM, not re-encoded to AAC, for two reasons. It is
    the only thing that keeps the sample count exactly equal — an AAC encoder
    adds priming samples and padding, which would make the length self-check
    below either fail or have to be loosened into uselessness. And this is a
    working file the next stage consumes, so a generation of lossy audio here
    buys nothing. It is bigger; it is also git-ignored and deletable.
    """
    interleaved = np.clip(audio, -1.0, 1.0).astype(np.float32).tobytes()
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-y",
         "-i", str(source),
         "-f", "f32le", "-ar", str(rate), "-ac", str(audio.shape[1]), "-i", "-",
         "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "pcm_s24le",
         str(destination)],
        input=interleaved, capture_output=True,
    )
    if result.returncode != 0:
        destination.unlink(missing_ok=True)   # never leave half a file to be reused
        sys.exit(f"could not write {destination.name}:\n"
                 f"{result.stderr.decode().strip()}")


def verify(source: Path, written: Path) -> None:
    """
    Three checks, and any one of them stops the run.

    These were written for the re-encode risk. They catch a deletion just as
    well, whatever caused it — which is what makes "divide to treat, never
    delete" hold by construction rather than by good intentions.
    """
    before, after = lib.probe_audio(source), lib.probe_audio(written)

    if before.get("sample_rate") != after.get("sample_rate") or \
       before.get("channels") != after.get("channels"):
        sys.exit(
            f"the audio changed shape and the run stops here.\n"
            f"  in:  {before.get('sample_rate')} Hz, {before.get('channels')} ch\n"
            f"  out: {after.get('sample_rate')} Hz, {after.get('channels')} ch\n"
            "  CapCut must receive the same shape it exported.")

    if before.get("samples") != after.get("samples"):
        sys.exit(
            f"the audio changed length and the run stops here.\n"
            f"  {before.get('samples')} samples in, {after.get('samples')} out\n"
            "  Every sample that went in must come out, in the same position.\n"
            "  Nothing in this tool may remove audio, for any reason.")

    if abs(lib.probe_duration(written) - lib.probe_duration(source)) > 0.05:
        sys.exit(
            f"the picture and the audio no longer start together.\n"
            f"  {lib.probe_duration(source):.3f}s in, "
            f"{lib.probe_duration(written):.3f}s out")
