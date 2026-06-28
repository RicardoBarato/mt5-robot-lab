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

OPERATOR_GATE_ARTIFACTS = {
    "reports/public/operator_gate_preview.json",
    "reports/public/operator_gate_preview.md",
}

OPERATOR_GATE_FORBIDDEN_TERMS = [
    "password",
    "token",
    "secret",
    "account_number",
    "broker_password",
    "real account",
    ".env",
    ".set",
    ".ex5",
]

FORBIDDEN_CLAIMS = [
    "guaranteed profit",
    "guaranteed live trading",
    "profit guaranteed",
    "guaranteed winner",
    "risk-free trading",
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
        rel_text = path.relative_to(root).as_posix()
        reason = is_forbidden(path, root)
        if reason:
            findings.append({"file": str(path.relative_to(root)), "reason": reason})
        if path.suffix.lower() in {".md", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for claim in FORBIDDEN_CLAIMS:
                if claim in text:
                    findings.append({"file": str(path.relative_to(root)), "reason": f"forbidden_claim:{claim}"})
        if rel_text in OPERATOR_GATE_ARTIFACTS:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for term in OPERATOR_GATE_FORBIDDEN_TERMS:
                if term in text:
                    findings.append({"file": rel_text, "reason": f"operator_gate_forbidden_term:{term}"})
    licensing_policy = root / "docs" / "LICENSING_POLICY.md"
    if licensing_policy.exists():
        text = licensing_policy.read_text(encoding="utf-8", errors="ignore").lower()
        if "not legal advice" not in text:
            findings.append({"file": "docs/LICENSING_POLICY.md", "reason": "missing_not_legal_advice"})
        if "do not restrict commercial use" not in text:
            findings.append({"file": "docs/LICENSING_POLICY.md", "reason": "missing_commercial_use_boundary"})
    submission_terms = root / "docs" / "SUBMISSION_TERMS_DRAFT.md"
    if submission_terms.exists():
        text = submission_terms.read_text(encoding="utf-8", errors="ignore").lower()
        if "draft" not in text or "not final legal terms" not in text:
            findings.append({"file": "docs/SUBMISSION_TERMS_DRAFT.md", "reason": "submission_terms_not_clearly_draft"})
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
