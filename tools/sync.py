#!/usr/bin/env python3
"""
sync.py — the one command to run after changing anything.

Two chores, in the order that catches a problem earliest:

  1. CHECK SYNTAX, so a typo surfaces the moment it is made rather than eight
     minutes into a render.
  2. RUN THE FIXTURE CHECKS, if anything moved that could change their outcome.

    python3 tools/sync.py                  both, over everything
    python3 tools/sync.py path [path ...]  only what those files affect
    python3 tools/sync.py --quiet ...      say nothing unless there is news

The `.claude/` hook calls the quiet form after every edit. Running it by hand
does exactly the same work — the hook is a trigger, not the logic.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Anything under these directories can change what the fixture checks conclude:
# `stages/` holds the pipeline, `_config/` holds the rules and the geometry
# arithmetic, and `memory/` holds the preference overrides whose whole job is to
# change the caption output.
CHECK_DIRS = {"stages", "_config", "memory"}
CHECK_FILES = {"pipeline_lib.py", "caption.py",
               "tools/make_fixture.py", "tools/run_fixture_checks.py"}


def relative(path: Path) -> str | None:
    """Path relative to the workspace, or None if it lives outside it."""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return None


def affects_checks(path: Path) -> bool:
    rel = relative(path)
    if rel is None:
        return False
    return rel.split("/")[0] in CHECK_DIRS or rel in CHECK_FILES


def syntax_error(path: Path) -> str | None:
    """Compile the source without importing it — nothing in the file runs."""
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except SyntaxError as exc:
        return f"syntax error  {relative(path) or path.name}:{exc.lineno}  {exc.msg}"
    except OSError as exc:
        return f"unreadable    {relative(path) or path.name}  {exc}"
    return None


def every_script() -> list[Path]:
    return sorted(
        path for path in ROOT.rglob("*.py")
        if not {"__pycache__", "runs", "node_modules"} & set(path.parts)
    )


def run_checks() -> tuple[bool, str]:
    fixture = subprocess.run(
        [sys.executable, str(ROOT / "tools/make_fixture.py")],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    if fixture.returncode != 0:
        return False, "make_fixture.py failed:\n" + (fixture.stdout + fixture.stderr).strip()

    checks = subprocess.run(
        [sys.executable, str(ROOT / "tools/run_fixture_checks.py")],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    output = checks.stdout + checks.stderr
    tally = next((line.strip() for line in output.splitlines() if "passed," in line),
                 "ran, but printed no tally")
    if checks.returncode == 0:
        return True, tally

    failures = [line.strip() for line in output.splitlines() if line.strip().startswith("FAIL")]
    return False, "\n".join([tally] + failures)


def main():
    argv = sys.argv[1:]
    quiet = "--quiet" in argv
    targets = [Path(arg).resolve() for arg in argv if not arg.startswith("-")]
    everything = not targets

    news: list[str] = []
    trouble = False

    # 1. Syntax.
    to_compile = (every_script() if everything
                  else [p for p in targets if p.suffix == ".py" and p.is_file()])
    broken = False
    for path in to_compile:
        error = syntax_error(path)
        if error:
            broken = True
            news.append(error)
            trouble = True

    # 2. The checks.
    if not broken and (everything or any(affects_checks(p) for p in targets)):
        ok, report = run_checks()
        news.append("checks        " + report.replace("\n", "\n              "))
        trouble = trouble or not ok

    if news:
        print("\n".join("  " + line for line in news))
    elif not quiet:
        print("  nothing to do — nothing changed that either chore cares about")

    sys.exit(1 if trouble else 0)


if __name__ == "__main__":
    main()
