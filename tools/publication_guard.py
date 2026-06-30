#!/usr/bin/env python3
"""Public safety guard for MT5 Robot Lab."""

from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
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

SENSITIVE_TERMS = [
    "password",
    "token",
    "secret",
    "account_number",
    "broker_password",
    "private_key",
    "api_key",
    "real account",
    ".env",
    ".set",
    ".ex5",
    ".tst",
]
OPERATOR_GATE_FORBIDDEN_TERMS = SENSITIVE_TERMS

TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".json",
    ".csv",
    ".py",
    ".yml",
    ".yaml",
    ".toml",
}

SCAN_ROOTS = (
    "reports/public/",
    "app/",
    "tools/",
    "tests/",
    "docs/",
    "factory/",
    ".github/workflows/",
)

PRIVATE_PATH_PATTERNS = [
    re.compile(r"(?i)[a-z]:[\\/]users[\\/]"),
    re.compile(r"(?i)(\\\\|//)[^\\/\s]+[\\/][^\\/\s]+"),
    re.compile(r"(?i)file://"),
    re.compile(r"(?i)\bappdata\b"),
    re.compile(r"(?i)\bdocuments[\\/]"),
    re.compile(r"(?i)%userprofile%"),
    re.compile(r"(?i)%appdata%"),
    re.compile(r"(?i)%localappdata%"),
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

SKIP_PREFIXES = {
    "reports/private/",
    "runs/",
}


def should_skip(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    rel_text = rel.as_posix()
    if bool(set(rel.parts) & SKIP_DIRS):
        return True
    if any(rel_text.startswith(prefix) for prefix in SKIP_PREFIXES):
        return True
    return _is_git_ignored(path, root) and not _is_public_scan_path(rel_text)


def _is_git_ignored(path: Path, root: Path) -> bool:
    if not (root / ".git").exists():
        return False
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return True
    completed = subprocess.run(
        ["git", "check-ignore", "-q", "--", rel],
        cwd=root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode == 0


def _is_public_scan_path(rel_text: str) -> bool:
    return rel_text == "README.md" or any(rel_text.startswith(prefix) for prefix in SCAN_ROOTS)


def is_forbidden(path: Path, root: Path) -> str | None:
    rel = path.relative_to(root)
    rel_text = rel.as_posix()
    if path.name in FORBIDDEN_NAMES:
        return "forbidden_name"
    if any(fnmatch.fnmatch(path.name, pattern) for pattern in FORBIDDEN_PATTERNS):
        return "forbidden_pattern"
    return None


def _is_scoped_text_file(path: Path, root: Path) -> bool:
    rel_text = path.relative_to(root).as_posix()
    return path.suffix.lower() in TEXT_EXTENSIONS and (
        rel_text in {"README.md"} or any(rel_text.startswith(prefix) for prefix in SCAN_ROOTS)
    )


def _allowed_sensitive_context(line: str, rel_text: str) -> bool:
    normalized = " ".join(line.lower().split())
    if rel_text.startswith("tests/"):
        return True
    if rel_text in {
        "tools/publication_guard.py",
        "app/core/mt5_detection.py",
        "app/core/submission_package.py",
        "app/core/champion_dna.py",
        "app/core/leaderboard_schema.py",
        "app/core/real_mt5_preflight.py",
        "app/core/real_mt5_runtime_contract.py",
        "app/core/mt5_terminal_runtime_diagnostics.py",
        "app/core/mt5_datadir_resolver.py",
        "app/core/compiled_ex5_readiness.py",
        "app/core/compiled_ex5_terminal_bootstrap.py",
        "app/core/terminal_contract_audit.py",
    }:
        return True
    if "design token" in normalized or "design_tokens" in normalized or rel_text == "app/ui/design_tokens.py":
        return True
    if "public_summary.lower" in normalized:
        return True
    if any(placeholder in normalized for placeholder in ["<user_home>", "<local_appdata>", "<appdata>", "<windows_path_redacted>", "<network_path_redacted>", "<file_uri_redacted>"]):
        return True
    if (rel_text == "README.md" or rel_text.startswith("docs/")) and normalized.startswith("- "):
        return True
    if (rel_text == "README.md" or rel_text.startswith("docs/")) and normalized.startswith(
        ("credentials", "server details", "passwords", "broker/account details")
    ):
        return True
    policy_markers = [
        "do not",
        "does not",
        "must not",
        "must never",
        "never",
        "not a",
        "not an",
        "not include",
        "not allowed",
        "not store",
        "not stored",
        "not uploaded",
        "no credentials",
        "no account",
        "sem senha",
        "nao armazena",
        "não armazena",
        "nao pede",
        "não pede",
        "forbidden",
        "denylist",
        "guard",
        "blocked",
        "redact",
        "redacted",
        "placeholder",
        "detect",
        "scanner",
        "scan",
        "sensitive",
        "private path",
        "private artifacts",
        "public artifacts",
        "public-safe",
        "claims are outside",
        "expected finding",
        "assert",
        "write_text",
        "contains no",
        "contains sensitive",
        "forbidden content",
        "forbidden artifact",
        "forbidden public text",
        "required before",
        "reject",
        "rejected",
    ]
    if any(marker in normalized for marker in policy_markers):
        return True
    if rel_text.startswith("tests/") and any(marker in normalized for marker in {"tmp", "bad", "leak", "finding"}):
        return True
    if rel_text == "tools/publication_guard.py":
        return True
    return False


def _scan_text(path: Path, root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    rel_text = path.relative_to(root).as_posix()
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return [{"file": rel_text, "reason": "unreadable_text_file"}]

    for number, line in enumerate(lines, start=1):
        lower_line = line.lower()
        for claim in FORBIDDEN_CLAIMS:
            if claim in lower_line and not _allowed_sensitive_context(line, rel_text):
                findings.append({"file": rel_text, "reason": f"forbidden_claim:{claim}:line:{number}"})
        for term in SENSITIVE_TERMS:
            if term in lower_line and not _allowed_sensitive_context(line, rel_text):
                findings.append({"file": rel_text, "reason": f"sensitive_term:{term}:line:{number}"})
                break
        if any(pattern.search(line) for pattern in PRIVATE_PATH_PATTERNS) and not _allowed_sensitive_context(line, rel_text):
            findings.append({"file": rel_text, "reason": f"private_path:line:{number}"})
    return findings


def scan(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in root.rglob("*"):
        if path.is_dir() or should_skip(path, root):
            continue
        rel_text = path.relative_to(root).as_posix()
        reason = is_forbidden(path, root)
        if reason:
            findings.append({"file": str(path.relative_to(root)), "reason": reason})
        if _is_scoped_text_file(path, root):
            findings.extend(_scan_text(path, root))
        elif rel_text in OPERATOR_GATE_ARTIFACTS:
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
