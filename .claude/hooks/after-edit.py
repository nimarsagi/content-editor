#!/usr/bin/env python3
"""
after-edit.py — fires after every file edit, runs the chores, reports back.

This is a trigger and nothing more. All the work lives in `tools/sync.py`, so
the behaviour is identical whether the hook fires or somebody runs it by hand —
there is no logic here that only exists inside the hook.

It always exits 0. A chore failing is news to be reported, not a reason to
block an edit that was already made; sync.py's own exit code says whether
anything is wrong, and that reaches the assistant as text either way.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0

    tool_input = event.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not path:
        return 0

    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/sync.py"), "--quiet", str(path)],
            capture_output=True, text=True, cwd=str(ROOT), timeout=120,
        )
        report = (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        report = "sync.py timed out after 120s — the fixture checks normally take under a second"
    except Exception as exc:
        report = f"sync.py could not be run — {exc}"

    if not report:
        return 0

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "tools/sync.py, after that edit:\n" + report,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
