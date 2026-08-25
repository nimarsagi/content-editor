"""
pipeline_lib.py — the shared plumbing every stage uses.

Engine, not a stage. It exists so that config loading, preference overrides, and
run-folder paths are written once rather than five times. It holds no thresholds
and no paths of its own — it only reads _config/.

The one rule it enforces on every caller: a stage reads a value from config or
from preferences, never from a literal in its own source.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CONFIG_DIR = ROOT / "_config"
MEMORY_DIR = ROOT / "memory"

# Everything a run produces sits under output/: the trail in output/runs/, the
# calibrated audio in output/audio/. Moved here 2026-08-01 when the audio stage
# gave the workspace a second kind of output — one folder to clear, one line in
# .gitignore, and the two kinds sit beside each other rather than one being a
# top-level folder and the other buried.
OUTPUT_DIR = ROOT / "output"
RUNS_DIR = OUTPUT_DIR / "runs"

# The same path as the console prints it. Derived rather than typed out at each
# print site, so moving the folder again is this line and nothing else — the
# step list in caption.py is the standing example of what a second copy costs.
RUNS_REL = RUNS_DIR.relative_to(ROOT).as_posix()


# ---------------------------------------------------------------- config


def _require_yaml():
    try:
        import yaml  # noqa
        return yaml
    except ImportError:
        sys.exit(
            "PyYAML is not installed.\n"
            "  pip3 install -r requirements.txt"
        )


def load_config() -> dict:
    """_config/edit-defaults.yaml — the rules and the diagnostics."""
    yaml = _require_yaml()
    with open(CONFIG_DIR / "edit-defaults.yaml", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if "rules" not in cfg or "diagnostics" not in cfg:
        sys.exit(
            "edit-defaults.yaml has lost its rules/diagnostics split.\n"
            "That split is the file's most important structure — a flat list is\n"
            "what let four caption values sit together looking equally binding\n"
            "when they could not all be true at once. Restore it before running."
        )
    return cfg


def rules() -> dict:
    return load_config()["rules"]


def diagnostics() -> dict:
    return load_config()["diagnostics"]


def load_paths() -> dict:
    yaml = _require_yaml()
    with open(CONFIG_DIR / "paths.yaml", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_lexicon() -> list[str]:
    """Known terms that seed transcription. Comments and blanks ignored."""
    path = CONFIG_DIR / "lexicon.txt"
    if not path.exists():
        return []
    terms = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            terms.append(line)
    return terms


# ----------------------------------------------------- learned preferences


_OVERRIDE_LINE = re.compile(r"^\*\*Override:\*\*\s*(.+)$", re.M)
_OVERRIDE = re.compile(r"`([A-Za-z_][\w.]*)`\s*(?:=|->|→|:)\s*([-\d.]+)")


def load_preferences(section: str) -> dict:
    """
    Read one section of memory/preferences.md and return the threshold overrides
    it states, plus the raw text of every rule in it.

    An Override line names one dotted key from _config/edit-defaults.yaml and
    the value to use instead, for this deployment:

        **Override:** raise `caption.min_duration_s` = 0.8

    Anything that is not a numeric override comes back as prose in `["text"]`,
    unread by anything. An override in a section nothing reads does nothing —
    see the table in preferences.md.
    """
    path = MEMORY_DIR / "preferences.md"
    if not path.exists():
        return {"overrides": {}, "text": []}

    body = path.read_text(encoding="utf-8")
    # Grab from "## <section>" to the next "## " at the same level.
    match = re.search(
        rf"^##\s+{re.escape(section)}\s*$(.*?)(?=^##\s|\Z)", body, re.M | re.S
    )
    if not match:
        return {"overrides": {}, "text": []}

    chunk = match.group(1)
    overrides: dict[str, float] = {}
    texts: list[str] = []
    for line_text in _OVERRIDE_LINE.findall(chunk):
        texts.append(line_text.strip())
        for key, value in _OVERRIDE.findall(line_text):
            overrides[key] = float(value) if "." in value else int(value)
    return {"overrides": overrides, "text": texts}


def apply_overrides(cfg_rules: dict, overrides: dict) -> dict:
    """Overlay dotted-key overrides from preferences onto the config rules."""
    for dotted, value in overrides.items():
        node = cfg_rules
        parts = dotted.split(".")
        for part in parts[:-1]:
            if part not in node or not isinstance(node[part], dict):
                print(f"  ! preferences override {dotted!r} names nothing in config — ignored")
                node = None
                break
            node = node[part]
        if node is None:
            continue
        if parts[-1] not in node:
            print(f"  ! preferences override {dotted!r} names nothing in config — ignored")
            continue
        print(f"  · preferences override: {dotted} {node[parts[-1]]} -> {value}")
        node[parts[-1]] = value
    return cfg_rules


# ------------------------------------------------------------- run folder


def run_dir(slug: str, create: bool = False) -> Path:
    """output/runs/[slug]/ — one run's whole trail, ordered by stage-number prefix."""
    path = RUNS_DIR / slug
    if create:
        path.mkdir(parents=True, exist_ok=True)
    elif not path.exists():
        sys.exit(f"no run folder at {path}")
    return path


def read_json(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data) -> Path:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    print(f"  wrote {path.relative_to(ROOT)}")
    return path


def require(path: Path, produced_by: str):
    """Fail loudly and specifically when a stage's input is missing."""
    if not path.exists():
        sys.exit(
            f"missing {path.name} in {path.parent.name}/\n"
            f"  It is produced by {produced_by}. Run that first."
        )
    return path


# ------------------------------------------------------------------ media


def probe_duration(media: Path) -> float:
    """Seconds, via ffprobe. The only thing in this build that opens the media."""
    out = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(media),
        ],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit(f"ffprobe failed on {media.name}:\n{out.stderr.strip()}")
    return float(out.stdout.strip())


def probe_frame_rate(media: Path) -> float:
    """
    Frames per second, via ffprobe.

    ffprobe reports this as a fraction — "30/1", or "30000/1001" for the 29.97
    that phones and editors both produce. Rounding 29.97 to 30 drifts by a frame
    every thirty-three seconds, so at the end of a two-minute take a caption
    lands four frames late. Divided, never rounded.
    """
    out = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(media),
        ],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit(f"ffprobe failed on {media.name}:\n{out.stderr.strip()}")
    raw = out.stdout.strip()
    if "/" in raw:
        numerator, denominator = raw.split("/", 1)
        if float(denominator) == 0:
            sys.exit(f"{media.name} reports a frame rate of {raw}, which cannot be used.")
        return float(numerator) / float(denominator)
    return float(raw)


def probe_codec(media: Path) -> str:
    """
    The video stream's codec name — "h264", "hevc", "prores", ...

    Asked because the renderer runs in Chromium, which decodes h264 and very
    little else. Phones shoot HEVC by default, and HEVC does not fail loudly
    there: the compositor stalls, and the render dies minutes later at whatever
    frame it reached, blaming a font timeout. Better answered before the render.
    """
    out = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(media),
        ],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit(f"ffprobe failed on {media.name}:\n{out.stderr.strip()}")
    return out.stdout.strip()


def probe_audio(media: Path) -> dict:
    """
    The audio stream's sample rate, channel count and length in samples.

    Asked because these three are what an audio stage must hand back unchanged.
    Sample count rather than seconds on purpose: a duration in seconds is rounded
    at the container and can hide a drift of a few hundred samples, which is
    exactly the kind of slip that puts the voice a hair ahead of the picture.

    Returns an empty dict when the file has no audio stream at all, so a caller
    can tell "silent" apart from "different".
    """
    out = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=sample_rate,channels,duration_ts,time_base",
            "-of", "default=noprint_wrappers=1",
            str(media),
        ],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit(f"ffprobe failed on {media.name}:\n{out.stderr.strip()}")

    fields = dict(
        line.split("=", 1) for line in out.stdout.strip().splitlines() if "=" in line
    )
    if not fields.get("sample_rate"):
        return {}

    rate = int(fields["sample_rate"])
    # duration_ts is in time_base units, which for audio is normally 1/rate —
    # but never assume it, because a container that stores it otherwise would
    # turn a sample count into a silently wrong one.
    samples = None
    if fields.get("duration_ts", "N/A") != "N/A" and "/" in fields.get("time_base", ""):
        numerator, denominator = fields["time_base"].split("/", 1)
        seconds = int(fields["duration_ts"]) * float(numerator) / float(denominator)
        samples = int(round(seconds * rate))

    return {
        "sample_rate": rate,
        "channels": int(fields["channels"]),
        "samples": samples,
    }


def timecode(seconds: float) -> str:
    """h:mm:ss.mmm — for console output a human reads."""
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h}:{m:02d}:{s:02d}.{ms:03d}"
