#!/usr/bin/env python3
"""
segment.py — where the gain is allowed to change.

    python3 stages/01b_calibrate/scripts/segment.py <run-slug>

Run directly it writes nothing and prints what it found: the boundaries it kept,
the level of each segment, and what correcting across them would do to the
spread. That is the honest test of a boundary — not whether it matches the cut
list.

THE PICTURE NOMINATES. LOUDNESS DECIDES. Scene-change scores propose positions
worth measuring and get no vote; a position survives only because the measured
speech level differs across it. That is what keeps this from being an editorial
judgement: the picture is asked where to look, never what is in the video.

SEGMENTING IS NOT EDITING, AND THE DIFFERENCE IS THE WHOLE RULE. "Whatever you
cut is based purely on averaging out the audio. Not content." A boundary here is
a place where the treatment changes. Nothing is removed, no picture moves, and
these boundaries never have to agree with the real cuts — agreement was only
ever a proxy for evenness, and evenness is what is actually measured.

WHY THE PICTURE IS CONSULTED AT ALL. A real cut moves the level by 1.0-2.9 dB,
while the frame-to-frame spread inside one clip is 6.9 dB. Hunting unknown
change points in that means testing hundreds of positions against a signal a
third the size of the noise, and it invents boundaries. Handed a position to
test, the same measurement is easy, because averaging a whole clip's voiced
frames collapses the uncertainty to +/- 0.35-0.61 dB.

WHAT IT GIVES UP. A cut joining two clips shot in the same place at the same
framing is invisible — one measured at a scene score of 0.005, indistinguishable
from camera shake. It is missed, and that costs nothing unless the level
actually differs across it. The `kept N of M` line is what makes a bad run
visible; see the measurement record in reference/ for the counts behind the
threshold.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline_lib as lib  # noqa: E402
import measure as mm  # noqa: E402

import numpy as np  # noqa: E402

_SCENE = re.compile(r"pts_time:([\d.]+)")

TALLY = lib.MEMORY_DIR / "boundary-tally.md"
_COUNTS = re.compile(r"^\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", re.M)

_TALLY_HEADER = """\
# boundary-tally.md — has the loudness check ever thrown a boundary away?

Three integers, kept across every run and rewritten in place. **Nothing reads
them to decide anything.** They are here to answer one question that no amount
of arguing can settle: is the loudness veto still earning its place, or is it
dead weight?

The veto exists to stop a false nomination becoming a boundary — camera shake, a
hand across the lens. Since the step started being measured at the join
(2026-08-14) neither of the two videos this was built on rejects anything, so
neither can tell *"the larger of the two steps"* apart from *"keep everything the
picture nominates"*. Only real footage over time can, and only if something is
counting. A printed line scrolls away and gets forgotten; this does not.

Every run prints these totals, and once `veto_review_after_videos` videos have
gone by with nothing rejected it says so in as many words. It still only prints.

**Exempt from `governance.md` rule 2 on the same ground as `caption-fixes.md`:
a record rather than a decision.** No per-run entries, nothing about any
individual video, no code path reads it back. Delete it and the next run starts
the count again — nothing else about the run changes.

| Videos processed | Boundaries nominated | Boundaries rejected |
|---|---|---|
"""


def nominate(video: Path, threshold: float) -> list[float]:
    """
    Positions in the picture worth measuring, by ffmpeg's scene score.

    No vote, only a nomination. The threshold is not trying to separate real
    cuts from false ones — it cannot: on one measured video the highest false
    score (0.336) sat above most of the real ones. It is only trying to keep the
    count near the number of cuts, so that every span handed to the loudness
    test is long enough to measure.
    """
    # metadata=print, not showinfo: showinfo logs at info level, which `-v error`
    # discards, so the filter appears to find nothing at all. This writes the
    # timestamps to stdout regardless of how loud ffmpeg has been told to be.
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video),
         "-filter:v", f"select='gt(scene,{threshold})',metadata=print:file=-",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.exit(f"scene detection failed on {video.name}:\n{result.stderr.strip()}")
    return sorted({round(float(m), 3) for m in _SCENE.findall(result.stdout)})


def word_gaps(words: list[dict]) -> list[tuple[float, float]]:
    """The silences between words. Where a gain change is allowed to happen."""
    gaps = []
    for earlier, later in zip(words, words[1:]):
        if later["start"] > earlier["end"]:
            gaps.append((earlier["end"], later["start"]))
    return gaps


def snap(positions: list[float], gaps: list[tuple[float, float]]) -> list[float]:
    """
    Move every nominated position to the middle of the nearest gap between words.

    A level change in the middle of a word is audible; the same change in the
    gap before it is not. The gaps are short but ample — median 0.24s and 0.15s
    on the two measured videos, against a ramp measured in tens of milliseconds.

    Two nominations landing in the same gap become one boundary. Nothing is
    gained by changing the gain twice in the same silence.
    """
    if not gaps:
        return []
    snapped = set()
    for position in positions:
        start, end = min(gaps, key=lambda g: 0.0 if g[0] <= position < g[1]
                         else min(abs(g[0] - position), abs(g[1] - position)))
        snapped.add(round((start + end) / 2, 3))
    return sorted(snapped)


def build(boundaries: list[float], duration: float) -> list[tuple[float, float]]:
    edges = [0.0] + list(boundaries) + [duration]
    return [(a, b) for a, b in zip(edges, edges[1:]) if b > a]


def measure_all(segments, db, is_speech, t):
    """Level and speech content of each segment, in one pass."""
    return [
        (mm.level(db, is_speech, a, b, t), mm.voiced_seconds(is_speech, a, b, t))
        for a, b in segments
    ]


def _merge(segments: list[tuple[float, float]], index: int):
    """Join segment `index` to the one after it."""
    joined = list(segments)
    joined[index:index + 2] = [(segments[index][0], segments[index + 1][1])]
    return joined


def settle(segments, db, is_speech, t, audio) -> tuple[list, list, list[str], int]:
    """
    Discard the boundaries the loudness does not support, and merge the segments
    that are too short to measure. Returns how many the loudness discarded.

    TWO PASSES, IN THIS ORDER, AND THE ORDER MATTERS. A segment with too little
    speech in it has no reliable level, so it must be absorbed before any step
    is judged against it — otherwise a meaningless level decides a real boundary.

    THE SECOND PASS IS GREEDY, WEAKEST STEP FIRST. Merging changes the levels
    either side, so the steps cannot all be judged at once against the levels
    they started with. Dropping the weakest boundary, re-measuring, and asking
    again is what makes the result independent of the order the boundaries
    happen to be in.

    A BOUNDARY IS JUDGED ON THE LARGER OF TWO STEPS (2026-08-14), because each
    catches a failure the other cannot see. The step measured AT THE JOIN finds
    a jump hidden by a clip's own fall across its length — 44.58s on the reel,
    whole-segment 0.99 dB against a join of 5.51, discarded, and audible. The
    step between WHOLE SEGMENT AVERAGES finds two clips that genuinely differ
    but happen to meet at a matching moment — 39.19s on the second video,
    whole-segment 3.94 dB against a join of 0.86. Taking the larger is strictly
    more permissive than either alone: it can keep a boundary, never discard one
    that survives today.
    """
    notes: list[str] = []

    # Pass one: a segment with too little speech joins the neighbour it is
    # CLOSEST TO IN LEVEL — not the nearer one in time. The point of the merge
    # is to avoid inventing a correction, and the nearer-in-level neighbour is
    # the one whose gain it can share without being wrong.
    while True:
        stats = measure_all(segments, db, is_speech, t)
        thin = next((i for i, (lvl, voiced) in enumerate(stats)
                     if lvl is None or voiced < audio["min_segment_s"]), None)
        if thin is None or len(segments) == 1:
            break
        before = stats[thin - 1][0] if thin > 0 else None
        after = stats[thin + 1][0] if thin + 1 < len(stats) else None
        mine = stats[thin][0]
        if before is None:
            target = thin                       # only a neighbour after it
        elif after is None:
            target = thin - 1                   # only a neighbour before it
        elif mine is None:
            target = thin - 1 if stats[thin - 1][1] >= stats[thin + 1][1] else thin
        else:
            target = thin - 1 if abs(mine - before) <= abs(mine - after) else thin
        notes.append(
            f"segment at {segments[thin][0]:.2f}s has "
            f"{stats[thin][1]:.2f}s of speech, under the "
            f"{audio['min_segment_s']:.2f}s needed to measure it — merged")
        segments = _merge(segments, target)

    # The step at each join, measured once. It is taken from the audio either
    # side of a fixed position, so unlike a whole-segment average it does not
    # move when a neighbouring segment is merged — which is what stops one
    # discarded boundary from dragging the next one down with it. That cascade
    # is how 38.78s was lost on the reel: a merge next door took its step from
    # 1.04 dB to 0.30 and it failed on the following pass.
    window = audio["boundary_window_s"]
    at_join = {end: mm.step_across(db, is_speech, t, end, window)
               for _, end in segments[:-1]}

    # Pass two: drop the weakest boundary until every surviving one is a real
    # step in level.
    rejected = 0
    while len(segments) > 1:
        levels = [lvl for lvl, _ in measure_all(segments, db, is_speech, t)]
        joins = [end for _, end in segments[:-1]]
        steps = [max(abs(after - before), at_join.get(join) or 0.0)
                 for (before, after), join in zip(zip(levels, levels[1:]), joins)]
        weakest = int(np.argmin(steps))
        if steps[weakest] >= audio["min_step_db"]:
            break
        rejected += 1
        segments = _merge(segments, weakest)

    return segments, measure_all(segments, db, is_speech, t), notes, rejected


def plan(levels: list[float], audio: dict) -> list[float]:
    """
    The between-clip gain each segment would get. Nothing is applied here.

    Each segment moves `between_segment_correction` of the way to the reference —
    not all of it. Emphasis put there deliberately is meant to survive; only the
    accidental mismatch is meant to go.
    """
    target = mm.reference(levels)
    cap = audio["max_correction_db"]
    return [float(np.clip((target - lvl) * audio["between_segment_correction"], -cap, cap))
            for lvl in levels]


def _stored_tally() -> tuple[int, int, int]:
    """The three running totals, or zeros if the file is not there yet."""
    if not TALLY.exists():
        return 0, 0, 0
    rows = _COUNTS.findall(TALLY.read_text(encoding="utf-8"))
    if not rows:
        return 0, 0, 0
    videos, seen, thrown = rows[-1]
    return int(videos), int(seen), int(thrown)


def keep_score(nominated: int, rejected: int, audio: dict) -> list[str]:
    """
    Add this run to the running count, and say what the count now shows.

    NOT CALLED BY THE DRY RUN, ON PURPOSE. `segment.py` run on its own writes
    nothing and must stay that way — it is the thing you use to try a setting
    without consequences. The counting belongs to runs that actually produced a
    file, so `calibrate_audio.py` calls this and the dry run never does.

    NOT A CHANGE LOG, WHICH WAS DECLINED OUTRIGHT: "I don't need a change log.
    I can hear myself whether it did a good job or not." Three integers with no
    per-run entries and nothing about any individual video is not a history of
    what happened — it is the answer to whether one check has ever fired.
    """
    videos, seen, thrown = _stored_tally()
    videos, seen, thrown = videos + 1, seen + nominated, thrown + rejected
    TALLY.parent.mkdir(parents=True, exist_ok=True)
    TALLY.write_text(f"{_TALLY_HEADER}| {videos} | {seen} | {thrown} |\n",
                     encoding="utf-8")

    said = [f"tally        {videos} video{'s' if videos != 1 else ''} so far, "
            f"{seen} boundaries nominated, {thrown} rejected by loudness"]
    if thrown == 0 and videos >= audio["veto_review_after_videos"]:
        said.append(f"the loudness check has never rejected a boundary in "
                    f"{videos} videos — it may be dead weight, and removing it "
                    f"is yours to decide")
    return said


def find(run: Path, video: Path, duration: float, words: list[dict], audio: dict):
    """Everything above, in order. Returns segments, levels, gains, notes."""
    nominated = nominate(video, audio["scene_threshold"])
    boundaries = snap(nominated, word_gaps(words))
    segments = build(boundaries, duration)

    x = mm.load(video, audio["highpass_hz"])
    t, db, is_speech = mm.speech_frames(x, words)

    segments, stats, notes, rejected = settle(segments, db, is_speech, t, audio)
    levels = [lvl for lvl, _ in stats]
    return {
        "nominated": nominated,
        "segments": segments,
        "levels": levels,
        "voiced": [v for _, v in stats],
        "gains": plan(levels, audio),
        "notes": notes,
        "rejected": rejected,
        "signal": (x, t, db, is_speech),
    }


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: segment.py <run-slug>")
    slug = sys.argv[1]
    run = lib.run_dir(slug)

    sys.path.insert(0, str(lib.ROOT / "stages" / "01_ingest" / "scripts"))
    from read_video import read_record  # noqa: E402

    audio = mm.settings()
    record = read_record(run)
    transcript = lib.read_json(lib.require(run / "01-transcript.json", "transcribe.py"))

    found = find(run, record["path"], record["duration"], transcript["words"], audio)
    segments, levels, gains = found["segments"], found["levels"], found["gains"]

    print(f"\n  boundaries   kept {len(segments) - 1} of "
          f"{len(found['nominated'])} nominated")
    for note in found["notes"]:
        print(f"  ! {note}")

    print("\n  segment            speech   level     would move")
    for (a, b), lvl, voiced, gain in zip(segments, levels, found["voiced"], gains):
        shown = f"{lvl:6.1f} dB" if lvl is not None else "     — "
        print(f"    {a:6.2f}-{b:6.2f}s   {voiced:5.2f}s  {shown}   {gain:+6.2f} dB")

    if levels and all(lvl is not None for lvl in levels):
        before = mm.spread(levels)
        after = mm.spread([lvl + gain for lvl, gain in zip(levels, gains)])
        print(f"\n  reference    {mm.reference(levels):6.1f} dBFS  "
              f"(mean of the segment levels, computed from this run)")
        print(f"  spread       {before:5.2f} dB  ->  {after:5.2f} dB   "
              f"quietest to loudest SEGMENT AVERAGE — "
              f"{'narrower' if after < before else 'NOT NARROWER — the boundaries are wrong'}")

        # And the same run measured the way it is heard. Both are printed
        # because the first one alone was misleading: it is computed from the
        # very averages the offsets are derived from, so it improves by
        # construction — 7.23 dB to 1.81 on the reel, while a clip that came in
        # loud was left exactly as it was.
        _x, t, db, is_speech = found["signal"]
        window_s = lib.diagnostics()["heard_window_s"]
        shift = np.zeros(len(t))
        for (start, end), gain in zip(segments, gains):
            shift[(t >= start) & (t < end)] = gain
        sd_before, band_before = mm.steadiness(
            mm.second_by_second(db, is_speech, t, window_s))
        sd_after, band_after = mm.steadiness(
            mm.second_by_second(db, is_speech, t, window_s, shift))
        print(f"  steadiness   {sd_before:5.2f} dB  ->  {sd_after:5.2f} dB   "
              f"how far the level strays from its own average, "
              f"{window_s:.0f}s at a time — THE ONE THE EAR FOLLOWS")
        print(f"               {band_before:5.2f} dB  ->  {band_after:5.2f} dB   "
              f"the band the middle 80% of the video sits in")
        print("               offsets only — the drift flattening inside each "
              "segment lands in calibrate_audio.py")

        print("\n  Nothing was written. This is the dry run.")


if __name__ == "__main__":
    main()
