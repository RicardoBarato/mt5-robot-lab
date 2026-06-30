"""Compiled EX5 readiness checks for terminal DataDir contracts.

This module does not launch MT5, MetaEditor, Strategy Tester, or compile an EA.
It validates metadata and ignored local readiness markers so a future real run
can prove that the Strategy Tester Expert value maps to the compiled EA inside
the same terminal DataDir.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from app.core.mt5_datadir_resolver import public_datadir_resolution_summary, resolve_terminal_datadir
from app.core.mt5_detection import redact_public_path


DEFAULT_READINESS_MARKER = Path("reports") / "private" / "local_readiness" / "compiled_ex5_readiness.local.json"
DEFAULT_MARKER_MAX_AGE_SECONDS = 7 * 24 * 60 * 60
WINDOWS_ABSOLUTE_RE = re.compile(r"(?i)^[a-z]:[\\/]")
DEFAULT_BOOTSTRAP_EXPERT = "Examples\\MACD Sample"
PUBLIC_BOOTSTRAP_JSON = Path("reports") / "public" / "compiled_ex5_readiness_bootstrap_summary.json"
PUBLIC_BOOTSTRAP_MD = Path("reports") / "public" / "compiled_ex5_readiness_bootstrap_summary.md"
PUBLIC_BOOTSTRAP_REPORT = (
    Path("reports") / "public" / "MVP_014K2_TERMINAL_DATADIR_EX5_BOOTSTRAP_REPORT.md"
)
PASS_BOOTSTRAP_STATUS = "PASS_MVP_014K2_TERMINAL_DATADIR_EX5_BOOTSTRAP_COMPLETED"
HOLD_DATADIR_STATUS = "HOLD_MVP_014K2_TERMINAL_DATADIR_NOT_FOUND"
HOLD_EX5_STATUS = "HOLD_MVP_014K2_EX5_NOT_FOUND_IN_TERMINAL_DATADIR"


@dataclass(frozen=True)
class CompiledEX5Readiness:
    terminal_data_dir_recorded: bool
    terminal_data_dir_consistent: bool
    expert_relative_path_set: bool
    expert_mapping_valid_for_strategy_tester: bool
    compiled_ex5_expected_path_configured: bool
    compiled_ex5_exists: bool
    compiled_ex5_verified_in_terminal_datadir: bool
    compiled_ex5_size: int | None
    compiled_ex5_mtime: float | None
    marker_found: bool
    marker_stale: bool
    marker_matches_terminal_contract: bool
    expert_parameters_status: str
    blocking_issues: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def normalize_expert_relative_path(expert: str) -> str:
    return str(expert or "").strip().replace("/", "\\").strip("\\")


def validate_expert_relative_path(expert: str) -> dict[str, object]:
    normalized = normalize_expert_relative_path(expert)
    issues: list[str] = []
    if not normalized:
        issues.append("expert_missing")
    if WINDOWS_ABSOLUTE_RE.search(normalized) or normalized.startswith("\\\\"):
        issues.append("expert_absolute_path_blocked")
    if normalized.lower().endswith((".ex5", ".mq5")):
        issues.append("expert_must_not_include_extension")
    if "reports\\private" in normalized.lower().replace("/", "\\"):
        issues.append("expert_must_not_point_to_private_reports")
    if any(part in {"", ".", ".."} for part in normalized.split("\\")) and normalized:
        issues.append("expert_relative_path_invalid")
    return {
        "expert_relative_path": normalized,
        "expert_relative_path_set": bool(normalized),
        "expert_format_valid": not issues,
        "blocking_issues": issues,
    }


def expected_ex5_relative_path(expert: str) -> Path:
    normalized = normalize_expert_relative_path(expert)
    return Path(*normalized.split("\\")).with_suffix(".ex5")


def expected_ex5_path_in_terminal_datadir(terminal_data_dir: str | Path, expert: str) -> Path:
    return Path(terminal_data_dir) / "MQL5" / "Experts" / expected_ex5_relative_path(expert)


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def marker_path(project_root: Path, override: Path | None = None) -> Path:
    return override or project_root / DEFAULT_READINESS_MARKER


def load_compiled_ex5_readiness_marker(project_root: Path, override: Path | None = None) -> dict[str, object]:
    path = marker_path(project_root, override)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"_error": "compiled_ex5_readiness_marker_unreadable"}
    return payload if isinstance(payload, dict) else {"_error": "compiled_ex5_readiness_marker_invalid"}


def write_compiled_ex5_readiness_marker(
    project_root: Path,
    *,
    terminal_install_id: str = "",
    terminal_fingerprint: str = "",
    terminal_data_dir: str | Path,
    expert_relative_path: str,
    override: Path | None = None,
    include_hash: bool = False,
    bootstrap_method: str = "",
) -> dict[str, object]:
    """Write an ignored local readiness marker for an already-compiled EX5.

    This helper is meant for operator/local preparation or tests. It does not
    compile anything and does not publish the marker.
    """

    expected_path = expected_ex5_path_in_terminal_datadir(terminal_data_dir, expert_relative_path)
    exists = expected_path.exists() and expected_path.is_file()
    stat = expected_path.stat() if exists else None
    payload: dict[str, object] = {
        "terminal_install_id": terminal_install_id,
        "terminal_fingerprint": terminal_fingerprint,
        "terminal_data_dir": str(Path(terminal_data_dir)),
        "expert_relative_path": normalize_expert_relative_path(expert_relative_path),
        "compiled_ex5_expected_path": str(expected_path),
        "compiled_ex5_exists": exists,
        "compiled_ex5_size": stat.st_size if stat else None,
        "compiled_ex5_mtime": stat.st_mtime if stat else None,
        "compiled_ex5_hash_optional": _hash_file(expected_path) if exists and include_hash else "",
        "marker_created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "bootstrap_method": bootstrap_method,
    }
    path = marker_path(project_root, override)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _marker_is_stale(marker: dict[str, object], max_age_seconds: int) -> bool:
    if max_age_seconds <= 0:
        return False
    created = str(marker.get("marker_created_at", "") or "")
    if not created:
        return True
    try:
        created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
    except ValueError:
        return True
    age = datetime.now(timezone.utc) - created_at.astimezone(timezone.utc)
    return age.total_seconds() > max_age_seconds


def _same_path(left: object, right: object) -> bool:
    left_text = str(left or "").replace("/", "\\").rstrip("\\").lower()
    right_text = str(right or "").replace("/", "\\").rstrip("\\").lower()
    return bool(left_text and right_text and left_text == right_text)


def _expert_parameters_status(
    terminal_data_dir: str,
    expert_parameters: str = "",
    *,
    expert_parameters_required: bool = False,
) -> tuple[str, list[str]]:
    value = str(expert_parameters or "").strip()
    if not value:
        if expert_parameters_required:
            return "missing_required", ["expert_parameters_missing"]
        return "not_required", []
    if WINDOWS_ABSOLUTE_RE.search(value) or value.startswith("\\\\"):
        return "invalid", ["expert_parameters_absolute_path_blocked"]
    if not terminal_data_dir:
        return "invalid", ["expert_parameters_datadir_missing"]
    candidate = Path(terminal_data_dir) / "MQL5" / "Profiles" / "Tester" / value
    if not candidate.exists() or not candidate.is_file():
        if expert_parameters_required:
            return "missing_required", ["expert_parameters_file_missing"]
        return "configured_but_not_found", []
    return "valid", []


def validate_compiled_ex5_readiness(
    project_root: Path,
    *,
    environment: dict[str, object] | None = None,
    expert_relative_path: str,
    readiness_marker: dict[str, object] | None = None,
    marker_override: Path | None = None,
    expert_parameters: str = "",
    expert_parameters_required: bool = False,
    marker_max_age_seconds: int = DEFAULT_MARKER_MAX_AGE_SECONDS,
    allow_external_filesystem_check: bool = False,
) -> dict[str, object]:
    env = environment or {}
    marker = readiness_marker if readiness_marker is not None else load_compiled_ex5_readiness_marker(project_root, marker_override)
    expert_validation = validate_expert_relative_path(expert_relative_path)
    expert = str(expert_validation["expert_relative_path"])
    terminal_data_dir = str(env.get("terminal_data_dir") or env.get("data_dir") or marker.get("terminal_data_dir") or "")
    expected_path = expected_ex5_path_in_terminal_datadir(terminal_data_dir, expert) if terminal_data_dir and expert else Path()
    marker_found = bool(marker) and not marker.get("_error")
    marker_stale = _marker_is_stale(marker, marker_max_age_seconds) if marker_found else False
    marker_expected_path = marker.get("compiled_ex5_expected_path", "")

    exists = bool(marker.get("compiled_ex5_exists", False)) if marker_found else False
    size = marker.get("compiled_ex5_size") if marker_found else None
    mtime = marker.get("compiled_ex5_mtime") if marker_found else None
    if allow_external_filesystem_check and expected_path:
        exists = expected_path.exists() and expected_path.is_file()
        if exists:
            stat = expected_path.stat()
            size = stat.st_size
            mtime = stat.st_mtime

    marker_matches = bool(
        marker_found
        and _same_path(marker.get("terminal_data_dir", ""), terminal_data_dir)
        and normalize_expert_relative_path(str(marker.get("expert_relative_path", ""))) == expert
        and _same_path(marker_expected_path, expected_path)
    )
    terminal_data_dir_recorded = bool(terminal_data_dir)
    terminal_data_dir_consistent = bool(terminal_data_dir_recorded and marker_matches)
    compiled_verified = bool(
        terminal_data_dir_consistent
        and marker_matches
        and exists
        and not marker_stale
        and bool(size is None or int(size) >= 0)
    )
    parameter_status, parameter_issues = _expert_parameters_status(
        terminal_data_dir,
        expert_parameters,
        expert_parameters_required=expert_parameters_required,
    )

    issues = [*list(expert_validation["blocking_issues"]), *parameter_issues]
    if not terminal_data_dir_recorded:
        issues.append("terminal_data_dir_missing")
    if not marker_found:
        issues.append("compiled_ex5_readiness_marker_missing")
    if marker.get("_error"):
        issues.append(str(marker["_error"]))
    if marker_stale:
        issues.append("compiled_ex5_readiness_marker_stale")
    if terminal_data_dir_recorded and not terminal_data_dir_consistent:
        issues.append("terminal_data_dir_mismatch")
    if expert and not exists:
        issues.append("compiled_ex5_not_found_in_terminal_datadir")
    if not compiled_verified:
        issues.append("compiled_ex5_not_verified_in_terminal_datadir")

    readiness = CompiledEX5Readiness(
        terminal_data_dir_recorded=terminal_data_dir_recorded,
        terminal_data_dir_consistent=terminal_data_dir_consistent,
        expert_relative_path_set=bool(expert_validation["expert_relative_path_set"]),
        expert_mapping_valid_for_strategy_tester=bool(expert_validation["expert_format_valid"] and marker_matches),
        compiled_ex5_expected_path_configured=expected_path != Path(),
        compiled_ex5_exists=exists,
        compiled_ex5_verified_in_terminal_datadir=compiled_verified,
        compiled_ex5_size=int(size) if isinstance(size, int) else None,
        compiled_ex5_mtime=float(mtime) if isinstance(mtime, (float, int)) else None,
        marker_found=marker_found,
        marker_stale=marker_stale,
        marker_matches_terminal_contract=marker_matches,
        expert_parameters_status=parameter_status,
        blocking_issues=list(dict.fromkeys(issues)),
        warnings=[],
    )
    payload = readiness.to_dict()
    payload["expert_relative_path"] = expert
    payload["compiled_ex5_expected_path_sanitized"] = (
        redact_public_path(expected_path).replace(".ex5", "<COMPILED_EA_FILE>") if expected_path else ""
    )
    return payload


def public_readiness_summary(readiness: dict[str, object]) -> dict[str, object]:
    return {
        "compiled_ex5_verified_in_terminal_datadir": bool(
            readiness.get("compiled_ex5_verified_in_terminal_datadir")
        ),
        "expert_relative_path_set": bool(readiness.get("expert_relative_path_set")),
        "terminal_datadir_consistent": bool(readiness.get("terminal_data_dir_consistent")),
        "marker_stale": bool(readiness.get("marker_stale")),
        "expert_mapping_valid_for_strategy_tester": bool(
            readiness.get("expert_mapping_valid_for_strategy_tester")
        ),
        "expert_parameters_status": str(readiness.get("expert_parameters_status", "")),
        "blocking_issues": list(readiness.get("blocking_issues", [])),
        "warnings": list(readiness.get("warnings", [])),
    }


def _sanitize_bootstrap_value(value: object) -> object:
    if isinstance(value, str):
        if not _looks_like_path(value):
            return value
        return redact_public_path(value).replace(".ex5", "<COMPILED_EA_FILE>").replace(".set", "<SET_FILE>")
    if isinstance(value, list):
        return [_sanitize_bootstrap_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_bootstrap_value(item) for key, item in value.items()}
    return value


def _looks_like_path(value: str) -> bool:
    text = value.strip()
    lowered = text.lower()
    return (
        ":\\" in text
        or ":/" in text
        or "\\" in text
        or "/" in text
        or lowered.startswith(("file://", "%appdata%", "%localappdata%", "%userprofile%"))
        or text.startswith(("\\\\", "//"))
    )


def sanitize_bootstrap_summary(payload: dict[str, object]) -> dict[str, object]:
    return {key: _sanitize_bootstrap_value(value) for key, value in payload.items()}


def build_compiled_ex5_readiness_bootstrap(
    project_root: Path,
    *,
    expert_relative_path: str = DEFAULT_BOOTSTRAP_EXPERT,
    include_hash: bool = False,
) -> dict[str, object]:
    """Resolve the terminal DataDir and create an ignored marker if EX5 exists."""

    resolution = resolve_terminal_datadir(project_root)
    data_dir_found = bool(resolution.get("terminal_data_dir_found"))
    data_dir = str(resolution.get("terminal_data_dir", "") or "")
    expert_validation = validate_expert_relative_path(expert_relative_path)
    expert = str(expert_validation["expert_relative_path"])
    expected_path = expected_ex5_path_in_terminal_datadir(data_dir, expert) if data_dir and expert else Path()
    ex5_exists = bool(expected_path and expected_path.exists() and expected_path.is_file())
    marker_created = False
    marker_payload: dict[str, object] = {}
    readiness: dict[str, object] = {}

    if data_dir_found and ex5_exists and bool(expert_validation["expert_format_valid"]):
        marker_payload = write_compiled_ex5_readiness_marker(
            project_root,
            terminal_install_id=Path(data_dir).name,
            terminal_fingerprint=Path(data_dir).name,
            terminal_data_dir=data_dir,
            expert_relative_path=expert,
            include_hash=include_hash,
        )
        marker_created = True
        readiness = validate_compiled_ex5_readiness(
            project_root,
            environment={"terminal_data_dir": data_dir},
            expert_relative_path=expert,
            readiness_marker=marker_payload,
        )
    else:
        readiness = validate_compiled_ex5_readiness(
            project_root,
            environment={"terminal_data_dir": data_dir} if data_dir else {},
            expert_relative_path=expert,
            readiness_marker={},
        )

    blocking_issues = list(
        dict.fromkeys(
            [
                *list(resolution.get("blocking_issues", [])),
                *list(expert_validation["blocking_issues"]),
                *list(readiness.get("blocking_issues", [])),
            ]
        )
    )
    if data_dir_found and not ex5_exists and "compiled_ex5_not_found_in_terminal_datadir" not in blocking_issues:
        blocking_issues.append("compiled_ex5_not_found_in_terminal_datadir")

    verified = bool(readiness.get("compiled_ex5_verified_in_terminal_datadir"))
    if verified:
        status = PASS_BOOTSTRAP_STATUS
        next_step = "review/merge MVP-014K2, then operator may approve MVP-014L one-run real retry only if terminal contract audit remains PASS"
    elif not data_dir_found:
        status = HOLD_DATADIR_STATUS
        next_step = "configure terminal_data_dir in ignored local config before retry"
    else:
        status = HOLD_EX5_STATUS
        next_step = "compile_or_copy_ex5_to_terminal_datadir_before_retry"

    payload = {
        "status": status,
        "datadir_resolver": True,
        "datadir_source": str(resolution.get("datadir_source", "")),
        "terminal_data_dir_found": data_dir_found,
        "terminal_data_dir_structure_valid": bool(resolution.get("terminal_data_dir_structure_valid")),
        "compiled_ex5_bootstrap_command": "PASS" if status == PASS_BOOTSTRAP_STATUS else "HOLD",
        "compiled_ex5_found_in_terminal_datadir": ex5_exists,
        "compiled_ex5_marker_created": marker_created,
        "compiled_ex5_verified_in_terminal_datadir": verified,
        "terminal_datadir_consistent": bool(readiness.get("terminal_data_dir_consistent")),
        "expert_relative_path": expert,
        "expert_relative_path_set": bool(expert_validation["expert_relative_path_set"]),
        "expert_mapping_valid_for_tester": bool(readiness.get("expert_mapping_valid_for_strategy_tester")),
        "marker_stale": bool(readiness.get("marker_stale")),
        "blocking_issues": blocking_issues,
        "warnings": list(dict.fromkeys([*list(resolution.get("warnings", [])), *list(readiness.get("warnings", []))])),
        "datadir_resolution": public_datadir_resolution_summary(resolution),
        "readiness": public_readiness_summary(readiness),
        "compiled_ex5_expected_path_sanitized": (
            redact_public_path(expected_path).replace(".ex5", "<COMPILED_EA_FILE>") if expected_path else ""
        ),
        "marker_path_sanitized": redact_public_path(marker_path(project_root)).replace(".json", "<JSON_MARKER>"),
        "mt5_real_run_new": False,
        "backtest_real_run_new": False,
        "strategy_tester_run_new": False,
        "ea_executed_new": False,
        "tournament_100_run": False,
        "exe_created": False,
        "zip_created": False,
        "credentials_stored": False,
        "private_files_committed": False,
        "ex5_committed": False,
        "set_committed": False,
        "paths_sanitized": True,
        "public_summary_created": True,
        "next_mvp": "MVP-014L One-run Real Retry With Terminal Contract Audit PASS",
        "next_step": next_step,
    }
    return sanitize_bootstrap_summary(payload)


def _bootstrap_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# MVP-014K2 Terminal DataDir and EX5 Readiness Bootstrap",
        "",
        f"- Status: {payload['status']}",
        f"- DataDir resolver: {str(payload['datadir_resolver']).lower()}",
        f"- DataDir source: {payload['datadir_source']}",
        f"- Terminal DataDir found: {str(payload['terminal_data_dir_found']).lower()}",
        f"- Compiled EX5 found in terminal DataDir: {str(payload['compiled_ex5_found_in_terminal_datadir']).lower()}",
        f"- Compiled EX5 marker created: {str(payload['compiled_ex5_marker_created']).lower()}",
        f"- Compiled EX5 verified in terminal DataDir: {str(payload['compiled_ex5_verified_in_terminal_datadir']).lower()}",
        f"- Terminal DataDir consistent: {str(payload['terminal_datadir_consistent']).lower()}",
        f"- Expert mapping valid for tester: {str(payload['expert_mapping_valid_for_tester']).lower()}",
        f"- Marker stale: {str(payload['marker_stale']).lower()}",
        f"- Blocking issues: {', '.join(payload['blocking_issues']) if payload['blocking_issues'] else 'none'}",
        f"- Warnings: {', '.join(payload['warnings']) if payload['warnings'] else 'none'}",
        "- MT5 real run new: false",
        "- Backtest real run new: false",
        "- Strategy Tester run new: false",
        "- EA executed new: false",
        "- Credentials stored: false",
        "- Private files committed: false",
        "- EX5 committed: false",
        "- SET committed: false",
        "- Paths sanitized: true",
        "",
        "This bootstrap is non-executing. It does not launch MT5, MetaEditor or Strategy Tester, and it does not compile or create an EX5.",
    ]
    return "\n".join(lines) + "\n"


def generate_compiled_ex5_readiness_bootstrap(project_root: Path) -> dict[str, object]:
    payload = build_compiled_ex5_readiness_bootstrap(project_root)
    public_json = project_root / PUBLIC_BOOTSTRAP_JSON
    public_md = project_root / PUBLIC_BOOTSTRAP_MD
    public_report = project_root / PUBLIC_BOOTSTRAP_REPORT
    public_json.parent.mkdir(parents=True, exist_ok=True)
    public_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown = _bootstrap_markdown(payload)
    public_md.write_text(markdown, encoding="utf-8")
    public_report.write_text(markdown, encoding="utf-8")
    return {
        "status": payload["status"],
        "summary": payload,
        "files": {
            "json": str(public_json),
            "markdown": str(public_md),
            "report": str(public_report),
        },
    }
