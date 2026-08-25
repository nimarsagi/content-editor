#!/usr/bin/env python3
"""
run_fixture_checks.py — run the pipeline on the fixture and assert the rules
that must never break.

These are the checks a script CAN make. The ones it cannot — whether the safe
zone actually clears the platform interfaces, whether the captions still line up
at the end of a long take — need eyes, and are listed at the end.

    python3 tools/make_fixture.py && python3 tools/run_fixture_checks.py
    python3 tools/run_fixture_checks.py --end-to-end     also: video in, file out

TWO SPEEDS, AND THAT IS A DELIBERATE TRADE (2026-08-01).

The fast checks run on a prepared transcript: no video is opened, nothing is
transcribed, nothing is rendered. They finish instantly, which is what lets the
`.claude/` hook run them after every single edit.

--end-to-end runs a real short video through `caption.py` itself — reading,
transcribing, chunking and rendering — and takes a minute or two. It is the only
check that would notice a new stage breaking the path from video to finished
file, because everything above it starts halfway along that path.

IT IS OPT-IN RATHER THAN ALWAYS-ON. Making it automatic would put a whisper load
and a Remotion render behind every keystroke, and a check slow enough to be
resented is a check that gets commented out. Run it at the points where breaking
the chain would matter: before and after a change to caption.py, pipeline_lib.py,
or any stage that opens the media.
"""

from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pipeline_lib as lib  # noqa: E402

SLUG = "fixture"
STEPS = [
    "stages/02_assemble/scripts/chunk_captions.py",
    "stages/02_assemble/scripts/write_srt.py",
]

E2E_SLUG = "endtoend"
E2E_VIDEO = lib.ROOT / "tools" / "fixtures" / "endtoend.mov"
E2E_TOPIC = "pricing your work as a consultant"

passed, failed = [], []


def check(name: str, condition: bool, detail: str = ""):
    (passed if condition else failed).append(name)
    print(f"  {'PASS' if condition else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))


def video_frames(media: Path) -> int:
    """Frames in the picture stream. Test-only, so it stays out of pipeline_lib."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-count_frames", "-show_entries", "stream=nb_read_frames",
         "-of", "default=noprint_wrappers=1:nokey=1", str(media)],
        capture_output=True, text=True,
    )
    return int(out.stdout.strip() or 0)


def end_to_end():
    """
    One short video through the whole chain, asserting the chain still joins up.

    WHAT THIS EXISTS TO CATCH. `caption.py` holds the step list, and the checks
    above hold a second copy of part of it. A stage added to one is invisible to
    the other, so a new step could break every real run while the fast checks
    stayed green. This runs `caption.py` itself, so there is only ever one list.

    WHAT IT ASSERTS ABOUT THE AUDIO, and why it is phrased the way it is. The
    comparison is between the file that went IN and the file the renderer
    actually consumed — not the rendered output, because Remotion re-encodes
    audio and normalises it to 48 kHz, so the finished file legitimately differs.
    Before an audio stage exists these are the same file and the check is
    trivially true. Once one exists, this is the assertion that it handed back
    the same audio it was given: same rate, same channels, same sample count.
    """
    print("\n  --- end to end: a video in, a captioned file out ---")

    if not E2E_VIDEO.exists():
        print(f"  building the fixture video (once) — {E2E_VIDEO.name}")
        built = subprocess.run(
            [sys.executable, str(lib.ROOT / "tools/make_fixture_video.py")],
            capture_output=True, text=True, cwd=str(lib.ROOT),
        )
        if built.returncode != 0:
            check("the fixture video builds", False,
                  (built.stdout + built.stderr).strip().splitlines()[-1])
            return

    source = lib.probe_audio(E2E_VIDEO)

    # A fresh run every time. The folder is regenerated output, and a stale
    # 01-transcript-raw.json left behind would be kept rather than rewritten —
    # transcribe.py protects that file on purpose — so the run would be graded
    # against a previous fixture.
    stale = lib.RUNS_DIR / E2E_SLUG
    if stale.exists():
        shutil.rmtree(stale)

    result = subprocess.run(
        [sys.executable, str(lib.ROOT / "caption.py"), str(E2E_VIDEO),
         "--topic", E2E_TOPIC, "--slug", E2E_SLUG],
        capture_output=True, text=True, cwd=str(lib.ROOT),
    )
    if result.returncode != 0:
        tail = (result.stdout + result.stderr).strip().splitlines()[-6:]
        check("the whole chain runs, video in to file out", False,
              "\n        ".join(tail))
        return
    check("the whole chain runs, video in to file out", True,
          f"{len(result.stdout.splitlines())} lines of step output")

    run = lib.RUNS_DIR / E2E_SLUG
    rendered = Path(lib.load_paths()["render_output"]).expanduser() / f"{E2E_SLUG}.mp4"
    check("a finished video exists at the end of it", rendered.is_file(),
          f"{rendered.stat().st_size / 1e6:.1f} MB" if rendered.is_file() else str(rendered))

    # The renderer reads its source from the transcript, so this is the file the
    # audio stage will have swapped in once it exists.
    transcript = lib.read_json(run / "01-transcript.json")
    consumed = Path(transcript["video"])
    check("the renderer's source video exists", consumed.is_file(), consumed.name)
    if not consumed.is_file():
        return

    got = lib.probe_audio(consumed)
    check("the audio going to the renderer has the same sample rate",
          got.get("sample_rate") == source.get("sample_rate"),
          f"{source.get('sample_rate')} in, {got.get('sample_rate')} out")
    check("the audio going to the renderer has the same channel count",
          got.get("channels") == source.get("channels"),
          f"{source.get('channels')} in, {got.get('channels')} out")
    # Sample count, not seconds: a container rounds seconds, and a few hundred
    # samples of drift is enough to put the voice ahead of the picture.
    check("the audio going to the renderer has the same length",
          got.get("samples") == source.get("samples"),
          f"{source.get('samples')} samples in, {got.get('samples')} out")

    # Frames, not seconds, and the video stream rather than the file. The
    # container's duration is the longest stream, and AAC pads the end of the
    # audio by ~0.1s, so comparing file durations reports a four-frame gap that
    # is not there. The renderer's own contract is exact: durationInFrames is
    # ceil(duration * fps), "so a final part-frame is not dropped".
    expected = math.ceil(lib.probe_duration(E2E_VIDEO) * lib.probe_frame_rate(E2E_VIDEO))
    check("the finished video is as long as the source",
          video_frames(rendered) == expected,
          f"{video_frames(rendered)} frames, expected {expected}")


def main():
    run = lib.run_dir(SLUG)
    for script in STEPS:
        result = subprocess.run([sys.executable, str(lib.ROOT / script), SLUG],
                                capture_output=True, text=True)
        if result.returncode != 0:
            sys.exit(f"{script} failed:\n{result.stdout}\n{result.stderr}")

    transcript = lib.read_json(run / "01-transcript.json")
    data = lib.read_json(run / "02-caption-cards.json")
    cards = data["cards"]
    cfg = lib.rules()
    cap = cfg["caption"]

    print("\n  --- rules that must hold ---")

    # The captions must say what was said. Nothing in this pipeline removes a
    # word, so a word going missing between the transcript and the screen would
    # be the tool quietly rewriting the take.
    spoken = [w["word"].strip() for w in transcript["words"]]
    captioned = " ".join(c["text"] for c in cards).split()
    check("every spoken word reaches a caption", len(spoken) == len(captioned),
          f"{len(spoken)} spoken, {len(captioned)} captioned")
    check("filler sounds are kept, not silently dropped",
          all(any(filler in c["text"] for c in cards) for filler in ("uhm", "ehh")),
          "nothing here cuts — the video arrives already cut")

    # Caption rules.
    check("no card exceeds the duration ceiling",
          all(c["duration"] <= cap["max_duration_s"] + 1e-3 for c in cards))
    check("no card exceeds the line count",
          all(len(c["lines"]) <= cap["max_lines"] for c in cards))

    chars = data["chars_per_line"]
    check("no line exceeds the derived character budget",
          all(len(line) <= chars for c in cards for line in c["lines"]), f"budget {chars}")

    # THE FLOOR IS NOT A BLANKET RULE, and that is deliberate (2026-07-31).
    #
    # Cards run wall-to-wall, so a card cannot be held past the one after it. The
    # only way to lift a short card over the floor is to join it into the card
    # before, and that fails whenever the joined text overruns the row — which at
    # one row of 25 characters is most of the time.
    #
    # So the rule is not "no card is under the floor". It is "no card that COULD
    # have been joined was left flashing". Re-running the join pass on what the
    # chunker produced must find nothing further to do.
    sys.path.insert(0, str(lib.ROOT / "stages" / "02_assemble" / "scripts"))
    import chunk_captions as cc  # noqa: E402

    groups, cursor = [], 0
    for card in cards:
        groups.append(transcript["words"][cursor:cursor + card["words"]])
        cursor += card["words"]
    _, further = cc.join_underfloor(groups, cap, chars)
    under = [c for c in cards if c["duration"] < cap["min_duration_s"] - 1e-3]
    check("every under-floor card that could be joined, was", further == 0,
          f"{len(under)} under the floor, none of them joinable"
          if under else "no card under the floor")

    # A caption holds until the next one starts, so it never flickers off in the
    # beat between phrases — but only up to the ceiling. Past that the video is
    # genuinely silent and the screen should be clean.
    gaps = [round(cards[i + 1]["start"] - cards[i]["end"], 3) for i in range(len(cards) - 1)]
    check("no gap between cards unless the video is silent past the ceiling",
          all(abs(g) < 1e-3 or cards[i]["duration"] >= cap["max_duration_s"] - 1e-3
              for i, g in enumerate(gaps)),
          f"{sum(1 for g in gaps if abs(g) >= 1e-3)} real silences")
    check("a silence longer than the ceiling is left uncaptioned",
          any(g > 1e-3 for g in gaps),
          "the fixture keeps one deliberate 3.2s beat")

    check("cards run in order and never overlap",
          all(cards[i]["end"] <= cards[i + 1]["start"] + 1e-3 for i in range(len(cards) - 1)))

    # Geometry, the arithmetic the anchor decision turned on.
    geo, typ = cfg["geometry"], cfg["typography"]
    bottom = geo["anchor_fraction"] * geo["canvas"][1] + \
        (typ["caption_size_px"] * 1.3 * cap["max_lines"]) / 2
    check("a full caption block clears the bottom safe margin",
          bottom <= geo["bottom_limit_px"], f"y={bottom:.0f} vs floor {geo['bottom_limit_px']}")
    check("a full-width line clears the right margin",
          geo["centre_x"] + geo["max_line_width_px"] / 2
          <= geo["canvas"][0] - geo["safe_zone"]["right"])
    check("characters per line is derived, not copied",
          chars == int(geo["max_line_width_px"] /
                       (typ["caption_size_px"] * geo["avg_char_advance_em"])))

    # The .srt is a real sidecar, not an empty file.
    srt = (run / "02-captions.srt").read_text(encoding="utf-8")
    check("the .srt has one block per card",
          srt.count(" --> ") == len(cards),
          f"{srt.count(' --> ')} blocks, {len(cards)} cards")

    # THE BOUNDARY TEST, ON A SIGNAL BUILT TO DEFEAT THE ONE IT REPLACES.
    #
    # Two stretches that each start loud and end quiet, in the same way. Their
    # averages are therefore identical, so a test comparing whole-segment
    # averages sees no step at the join and throws the boundary away — which is
    # what happened at 44.58s on a real reel and was heard as "the clip at 00:46
    # is a lot louder than the clip before". Measured at the join instead, the
    # step is 8 dB and the boundary survives.
    #
    # A SYNTHETIC LEVEL CURVE, NOT A FIXTURE VIDEO, because the fault is in the
    # arithmetic and this is the shape that exposes it. No real recording is
    # guaranteed to contain it.
    sys.path.insert(0, str(lib.ROOT / "stages" / "01b_calibrate" / "scripts"))
    import numpy as np  # noqa: E402
    import segment as sg  # noqa: E402

    audio = cfg["audio"]
    two = [(0.0, 10.0), (10.0, 20.0)]
    t = np.arange(0.0, 20.0, 0.01)                    # 10 ms frames, as measured
    speech = np.ones(len(t), dtype=bool)

    falling = -20.0 - 10.0 * ((t % 10.0) / 10.0)      # two identical 10 dB falls
    kept, _levels, _notes, _rejected = sg.settle(two, falling, speech, t, audio)
    check("a boundary is kept when the join steps but the clip averages match",
          len(kept) == 2, f"{len(kept)} segments out of 2")

    flat = np.full(len(t), -25.0)
    merged, _levels, _notes, rejected = sg.settle(two, flat, speech, t, audio)
    check("a boundary with no step by either measurement is still discarded",
          len(merged) == 1 and rejected == 1, f"{len(merged)} segments out of 2")

    # THE WITHIN-CLIP CORRECTION, ON A LEVEL THAT HUMPS RATHER THAN TILTS.
    #
    # This is the shape the straight line could not touch: loud in the middle,
    # quiet at both ends. A line fitted to it is flat and subtracts nothing, so
    # the hump survived every run and was heard as "some parts are significantly
    # louder than others". A correction that follows the level removes it.
    import apply_gain as ag  # noqa: E402

    spoken = [{"start": k * 0.5, "end": k * 0.5 + 0.4} for k in range(40)]
    hump = -25.0 + 6.0 * np.sin(np.pi * t[:2000] / 20.0)       # peaks mid-clip
    shifts = ag.flatten(spoken, list(range(len(spoken))), hump, speech[:2000],
                        t[:2000], (0.0, 20.0), 1.0, audio["drift_window_s"],
                        audio["min_drift_fit_s"])
    landed = []
    for i, word in enumerate(spoken):
        sel = speech[:2000] & (t[:2000] >= word["start"]) & (t[:2000] < word["end"])
        landed.append(float(np.median(hump[sel])) + shifts.get(i, 0.0))
    check("a clip that is loud in the MIDDLE is flattened, not just a tilt",
          max(landed) - min(landed) < 1.5,
          f"{max(hump) - min(hump):.1f} dB hump -> {max(landed) - min(landed):.2f} dB left")

    # And it must not move the clip's own average, or the between-clip offset
    # measured before it would no longer mean what it measured.
    check("the within-clip correction leaves the clip's average where it was",
          abs(float(np.mean(list(shifts.values())))) < 1e-9,
          f"mean shift {float(np.mean(list(shifts.values()))):.2e} dB")

    # Cost discipline. Every model call went with the cut detection; a run now
    # costs transcription and nothing else. A skill file appearing under stages/
    # means that changed.
    call_sites = [p for p in lib.ROOT.glob("stages/*/*.md")
                  if "SKILL" in p.read_text(encoding="utf-8")]
    check("no model call sites — a run costs nothing but transcription",
          not call_sites, ", ".join(p.name for p in call_sites))

    # The source specs stay unread by the pipeline.
    opens_specs = any("source-specs" in p.read_text(encoding="utf-8")
                      for p in lib.ROOT.glob("stages/*/scripts/*.py"))
    check("no runtime code path opens the source specs", not opens_specs)

    # Nothing left pointing at the editor that is no longer part of this.
    live = list(lib.ROOT.glob("stages/*/scripts/*.py")) + \
        [lib.ROOT / "caption.py", lib.ROOT / "pipeline_lib.py"]
    mentions = [p.name for p in live
                if "resolve" in p.read_text(encoding="utf-8")
                .lower().replace(".resolve()", "")]
    check("no pipeline script mentions Resolve", not mentions, ", ".join(mentions))

    # A delayRender() handle held at module scope turns the render timeout into a
    # hard ceiling on video length: its clock starts at page load and runs for the
    # whole render, so a long video dies mid-way blaming whatever it was waiting
    # for. That cost three failed renders of a two-minute take, at frames 905,
    # 1207 and 49, and NO short test can catch it — they finish before the timer.
    # This is the check that stands in for a long render.
    module_scope_delay = []
    for tsx in (lib.ROOT / "remotion" / "src").glob("*.tsx"):
        for number, line in enumerate(tsx.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith(("const ", "let ", "var ")) and "delayRender(" in line:
                module_scope_delay.append(f"{tsx.name}:{number}")
    check("no delayRender() handle is held at module scope",
          not module_scope_delay, ", ".join(module_scope_delay))

    # The same render also hung fetching the font over Remotion's static server
    # under concurrency. It is embedded as a data URI now; a staticFile() font
    # reference would put the request — and the hang — back.
    # Tested by the mechanism, not by the filename — the filename appears in the
    # comment explaining all this, which is not a fetch.
    root = (lib.ROOT / "remotion" / "src" / "Root.tsx").read_text(encoding="utf-8")
    code = "\n".join(line for line in root.splitlines()
                     if not line.lstrip().startswith(("*", "//", "/*")))
    check("the font is embedded, not fetched",
          "INTER_SEMIBOLD" in code and "staticFile" not in code)

    if "--end-to-end" in sys.argv:
        end_to_end()

    print(f"\n  {len(passed)} passed, {len(failed)} failed")
    if failed:
        print("\n  FAILED: " + "; ".join(failed))

    if "--end-to-end" not in sys.argv:
        print("\n  The chain from video to finished file was NOT exercised."
              "\n  Run `python3 tools/run_fixture_checks.py --end-to-end` after"
              "\n  touching caption.py, pipeline_lib.py, or any stage that opens media.")

    print("""
  Not checkable here — these need you:
    - the safe zone actually clears both platforms' interfaces, on-device
    - captions do not drift out of sync by the END of a long take
    - transcription is accurate enough on your real audio
    - the lexicon closes its loop across two real runs""")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
