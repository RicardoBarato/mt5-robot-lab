#!/usr/bin/env python3
"""Public safety guard for MT5 Robot Lab."""

from __future__ import annotations

import argparse
import fnmatch
import sys
from pathlib import Path


FORBIDDEN_NAMES = {
    "QUANTBOT_CONTEXT_RB_RISK_ENGINE.md",
    "MEMORY.md",
    ".env",
}

FORBIDDEN_PATTERNS = [
    "*.set",
    "*.ex5",
    ".env.*",
]

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
}


def should_skip(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    return bool(set(rel.parts) & SKIP_DIRS)


def is_forbidden(path: Path, root: Path) -> str | None:
    rel = path.relative_to(root)
    rel_text = rel.as_posix()
    if path.name in FORBIDDEN_NAMES:
        return "forbidden_name"
    if any(fnmatch.fnmatch(path.name, pattern) for pattern in FORBIDDEN_PATTERNS):
        return "forbidden_pattern"
    if rel_text.startswith("reports/private/") and path.name != ".gitkeep":
        return "private_report_artifact"
    return None


def scan(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in root.rglob("*"):
        if path.is_dir() or should_skip(path, root):
            continue
        reason = is_forbidden(path, root)
        if reason:
            findings.append({"file": str(path.relative_to(root)), "reason": reason})
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    findings = scan(root)
    if findings:
        for finding in findings:
            print(finding)
        return 1
    print("mt5_robot_lab_publication_guard_passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
