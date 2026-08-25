#!/usr/bin/env python3
"""
calibrate_audio.py — even out the levels on the export, and hand the next stage
the file it should use.

    python3 stages/01b_calibrate/scripts/calibrate_audio.py <run-slug>

Runs after transcribing and before caption cards. It needs the word timings
(levels are measured on speech only) and it must run before the render, which is
what picks the file up.

WHERE IT READS ITS INPUT, AND WHY IT MATTERS. It takes the source from
`01-video.md`, through the same `read_record()` call transcribe.py already makes.
It cannot take it from `01-transcript.json`'s "video" field, because that is the
field it OVERWRITES — after one run that field points at this stage's own output.
One file says where the original is, another says where the next stage should
look, and they cannot collide.

IT REFUSES TO PROCESS ITS OWN OUTPUT, AND STOPS RATHER THAN SKIPPING. Recognised
by location: a source sitting inside the audio output folder is this stage's own
work. No marker written into the file, no filename convention, nothing to keep in
sync. Stopping rather than carrying on is deliberate — a run that silently
skipped a step would produce a file that looks finished and is not.

NO MODEL IS CALLED. This is arithmetic on a waveform: deterministic, cheap, and
exactly reproducible. A run still costs transcription and nothing else.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "stages" / "01_ingest" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline_lib as lib  # noqa: E402
import measure as mm  # noqa: E402
import segment as sg  # noqa: E402
import apply_gain as ag  # noqa: E402
from read_video import read_record  # noqa: E402

import numpy as np  # noqa: E402


def destination(slug: str) -> Path:
    """output/audio/[slug]/ — from paths.yaml, never spelled out here."""
    paths = lib.load_paths()
    if "audio_output" not in paths:
        sys.exit(
            "_config/paths.yaml has no `audio_output`.\n"
            "  It is the only place a filesystem path may appear in this "
            "workspace, and this stage writes to one.")
    folder = Path(paths["audio_output"]).expanduser()
    if not folder.is_absolute():
        folder = lib.ROOT / folder
    folder = folder / slug
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def refuse_own_output(source: Path, audio_root: Path) -> None:
    """Stop if handed something this stage produced. See the module docstring."""
    try:
        source.resolve().relative_to(audio_root.resolve())
    except ValueError:
        return
    sys.exit(
        f"{source.name} is this stage's own output, and it will not be "
        f"processed again.\n"
        f"  It sits inside {audio_root.relative_to(lib.ROOT)}/.\n"
        "  Levelling an already-levelled file corrects against the wrong\n"
        "  reference and compounds every gain. The run stops here rather than\n"
        "  skipping the step, because a skipped step produces a file that\n"
        "  looks finished and is not.\n"
        "  The original is recorded in 01-video.md — restore it there.")


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: calibrate_audio.py <run-slug>")
    slug = sys.argv[1]
    run = lib.run_dir(slug)

    audio = mm.settings()
    unknown = mm.unknown_keys(lib.load_preferences("Audio")["overrides"], audio)
    for key in unknown:
        print(f"  ! audio rule `{key}` names no setting — ignored, not applied")

    record = read_record(run)
    source = record["path"]
    if not source.exists():
        sys.exit(f"the video has moved or been deleted:\n    {source}")

    out_dir = destination(slug)
    refuse_own_output(source, out_dir.parent)

    transcript_path = lib.require(run / "01-transcript.json", "transcribe.py")
    transcript = lib.read_json(transcript_path)
    words = transcript.get("words") or []
    if not words:
        sys.exit(
            "the transcript has no words in it.\n"
            "  Levels are measured on speech, so there is nothing to measure\n"
            "  against. Run transcribe.py first.")

    # ---- what to do -----------------------------------------------------
    found = sg.find(run, source, record["duration"], words, audio)
    segments, levels, offsets = found["segments"], found["levels"], found["gains"]
    _x, t, db, is_speech = found["signal"]

    print(f"  boundaries   kept {len(segments) - 1} of "
          f"{len(found['nominated'])} nominated")
    for note in found["notes"]:
        print(f"  ! {note}")

    capped = [i for i, g in enumerate(offsets)
              if abs(abs(g) - audio["max_correction_db"]) < 1e-6]
    for i in capped:
        print(f"  ! segment at {segments[i][0]:.2f}s hit the "
              f"{audio['max_correction_db']:.1f} dB correction cap — "
              "something upstream is probably wrong")

    # ---- the two corrections, per word ----------------------------------
    gains = [0.0] * len(words)
    for (start, end), offset in zip(segments, offsets):
        indices = [i for i, w in enumerate(words)
                   if start <= (w["start"] + w["end"]) / 2 < end]
        shifts = ag.flatten(words, indices, db, is_speech, t, (start, end),
                            audio["within_segment_correction"],
                            audio["drift_window_s"],
                            audio["min_drift_fit_s"])
        for i in indices:
            gains[i] = offset + shifts.get(i, 0.0)

    # ---- what it did, measured two ways ---------------------------------
    # BOTH, LABELLED, AND THAT IS THE POINT. The spread of the segment averages
    # is computed from the same averages the offsets are derived from, so it
    # improves by construction: it read 7.23 dB closing to 1.81 on a run whose
    # audible fault — a clip arriving loud — it could not see. The steadiness
    # figure is the level over one-second windows across the whole file, which
    # is roughly what the ear follows, and it moves only when the video does.
    before = mm.spread([lvl for lvl in levels if lvl is not None])
    after = mm.spread([lvl + g for lvl, g in zip(levels, offsets) if lvl is not None])
    print(f"  levels       spread {before:.2f} dB -> {after:.2f} dB "
          f"across {len(segments)} segments (segment averages)")

    window_s = lib.diagnostics()["heard_window_s"]
    shift = np.zeros(len(t))
    for word, gain in zip(words, gains):
        shift[(t >= word["start"]) & (t < word["end"])] = gain
    sd_before, band_before = mm.steadiness(
        mm.second_by_second(db, is_speech, t, window_s))
    sd_after, band_after = mm.steadiness(
        mm.second_by_second(db, is_speech, t, window_s, shift))
    print(f"  steadiness   {sd_before:.2f} dB -> {sd_after:.2f} dB, "
          f"middle 80% {band_before:.2f} dB -> {band_after:.2f} dB "
          f"({window_s:.0f}s at a time — what the ear follows)")
    print(f"  drift        flattened {audio['within_segment_correction']:.0%} "
          f"inside each segment")

    # ---- apply ----------------------------------------------------------
    shape = lib.probe_audio(source)
    if not shape:
        sys.exit(f"{source.name} has no audio stream to calibrate.")
    rate, channels = shape["sample_rate"], shape["channels"]

    signal = ag.decode_full(source, rate, channels, audio["highpass_hz"],
                            shape.get("samples"))
    curve = ag.envelope(words, gains, len(signal), rate, audio["ramp_ms"])
    signal = signal * (10 ** (curve / 20))[:, None]

    signal, engaged = ag.limit(signal, audio["peak_ceiling_dbtp"], rate,
                               audio["limiter_lookahead_ms"],
                               audio["limiter_release_ms"])
    if engaged > 0.005:
        print(f"  ! the limiter worked on {engaged:.1%} of the file — "
              "the levelling pushed something too hot")
    else:
        print(f"  limiter      {engaged:.2%} of the file, "
              f"ceiling {audio['peak_ceiling_dbtp']:.1f} dBTP")

    written = out_dir / f"{source.stem}-levelled{source.suffix}"
    ag.write(signal, source, written, rate)
    ag.verify(source, written)
    print(f"  wrote        {written.relative_to(lib.ROOT)}  "
          f"({written.stat().st_size / 1e6:.0f} MB)")

    # Counted here rather than up with the boundaries, so a run that fell over
    # before producing anything does not enter the count as a video processed.
    for line in sg.keep_score(len(found["nominated"]), found["rejected"], audio):
        print(f"  {line}")

    # ---- hand it to the next stage --------------------------------------
    transcript["video"] = str(written)
    lib.write_json(transcript_path, transcript)
    print("  next: chunk_captions.py")


if __name__ == "__main__":
    main()
