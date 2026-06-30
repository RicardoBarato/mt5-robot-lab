"""Bootstrap compiled EX5 readiness inside the resolved terminal DataDir.

This module is intentionally narrow. It never launches terminal64.exe, never
starts Strategy Tester and never executes an EA. It may copy a safe local source
or compiled file into the exact terminal DataDir target path, and it may invoke
MetaEditor only for a controlled compile when a safe source exists.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Callable, Protocol

from app.core.compiled_ex5_readiness import (
    DEFAULT_BOOTSTRAP_EXPERT,
    expected_ex5_path_in_terminal_datadir,
    marker_path,
    normalize_expert_relative_path,
    validate_compiled_ex5_readiness,
    validate_expert_relative_path,
    write_compiled_ex5_readiness_marker,
)
from app.core.mt5_datadir_resolver import public_datadir_resolution_summary, resolve_terminal_datadir
from app.core.mt5_detection import (
    LOCAL_MT5_CONFIG_PATH,
    redact_public_path,
    resolve_mt5_execution_paths,
    validate_mt5_executable_path,
)
from app.core.terminal_contract_audit import build_terminal_contract_audit


PUBLIC_TERMINAL_BOOTSTRAP_JSON = Path("reports") / "public" / "compiled_ex5_terminal_bootstrap_summary.json"
PUBLIC_TERMINAL_BOOTSTRAP_MD = Path("reports") / "public" / "compiled_ex5_terminal_bootstrap_summary.md"
PUBLIC_SAFE_SMOKE_BOOTSTRAP_JSON = Path("reports") / "public" / "safe_smoke_ea_bootstrap_summary.json"
PUBLIC_SAFE_SMOKE_BOOTSTRAP_MD = Path("reports") / "public" / "safe_smoke_ea_bootstrap_summary.md"
PUBLIC_TERMINAL_BOOTSTRAP_REPORT = (
    Path("reports") / "public" / "MVP_014K4_SAFE_SMOKE_EA_SOURCE_EX5_BOOTSTRAP_REPORT.md"
)

PASS_STATUS = "PASS_MVP_014K4_SAFE_SMOKE_EA_EX5_BOOTSTRAP_COMPLETED"
HOLD_DATADIR_STATUS = "HOLD_MVP_014K4_TERMINAL_DATADIR_NOT_FOUND"
HOLD_SOURCE_STATUS = "HOLD_MVP_014K4_MQL5_SOURCE_OR_EX5_NOT_FOUND"
HOLD_AMBIGUOUS_STATUS = "HOLD_MVP_014K4_EXPERT_SOURCE_AMBIGUOUS"
HOLD_METAEDITOR_STATUS = "HOLD_MVP_014K4_METAEDITOR_NOT_AVAILABLE"
HOLD_COMPILE_STATUS = "HOLD_MVP_014K4_METAEDITOR_COMPILE_FAILED"

METHOD_ALREADY_PRESENT = "already_present"
METHOD_COMPILED = "compiled_with_metaeditor"
METHOD_COPIED_EX5 = "copied_existing_local_ex5"
METHOD_HOLD_MISSING = "hold_missing_source_or_ex5"
METHOD_HOLD_AMBIGUOUS = "hold_expert_source_ambiguous"

SAFE_REPO_MQ5_ROOTS = (
    Path("MQL5") / "Experts",
    Path("app") / "assets" / "mql5",
    Path("src") / "mql5",
    Path("examples") / "mql5",
)


class CompileRunner(Protocol):
    def __call__(
        self,
        command: list[str],
        *,
        cwd: Path,
        timeout: int,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        ...


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _expected_mq5_path(terminal_data_dir: Path, expert_relative_path: str) -> Path:
    expert = normalize_expert_relative_path(expert_relative_path)
    return terminal_data_dir / "MQL5" / "Experts" / Path(*expert.split("\\")).with_suffix(".mq5")


def _read_local_config(project_root: Path) -> dict[str, str]:
    path = project_root / LOCAL_MT5_CONFIG_PATH
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    allowed = {
        "expert_relative_path",
        "compiled_ex5_source_mq5",
        "compiled_ex5_source_path",
        "compiled_ex5_local_ex5",
        "compiled_ex5_local_path",
    }
    return {key: str(payload.get(key, "") or "") for key in allowed if payload.get(key)}


def _resolve_config_path(project_root: Path, value: str) -> Path:
    expanded = os.path.expandvars(str(value or "").strip())
    candidate = Path(expanded)
    if not candidate.is_absolute():
        candidate = project_root / candidate
    return candidate


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except (OSError, ValueError):
        return False


def _is_forbidden_project_source(path: Path, project_root: Path) -> bool:
    if not _is_relative_to(path, project_root):
        return True
    rel = path.resolve().relative_to(project_root.resolve()).as_posix().lower()
    forbidden_prefixes = (
        "reports/private/",
        "runs/",
        "downloads/",
        "desktop/",
        "ea-auto-backtest-engine/",
        "ea-trader/",
        "payoffgrid/",
        "onpn11/",
    )
    return any(rel.startswith(prefix) for prefix in forbidden_prefixes)


def _git_ignored(path: Path, project_root: Path) -> bool:
    try:
        rel = path.resolve().relative_to(project_root.resolve())
    except (OSError, ValueError):
        return False
    completed = subprocess.run(
        ["git", "check-ignore", "-q", "--", rel.as_posix()],
        cwd=project_root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode == 0


def _safe_repo_mq5_candidates(project_root: Path, expert_relative_path: str) -> list[Path]:
    expected_rel = Path(*normalize_expert_relative_path(expert_relative_path).split("\\")).with_suffix(".mq5")
    candidates: list[Path] = []
    for root in SAFE_REPO_MQ5_ROOTS:
        candidate = project_root / root / expected_rel
        if candidate.exists() and candidate.is_file() and not _is_forbidden_project_source(candidate, project_root):
            candidates.append(candidate)
    return candidates


def _configured_mq5_candidates(
    project_root: Path,
    config: dict[str, str],
    target_mq5: Path,
) -> list[Path]:
    candidates: list[Path] = []
    for key in ("compiled_ex5_source_mq5", "compiled_ex5_source_path"):
        value = config.get(key, "")
        if not value:
            continue
        candidate = _resolve_config_path(project_root, value)
        if candidate.suffix.lower() != ".mq5" or not candidate.exists() or not candidate.is_file():
            continue
        if _same_file(candidate, target_mq5) or not _is_forbidden_project_source(candidate, project_root):
            candidates.append(candidate)
    return candidates


def _configured_ex5_candidates(
    project_root: Path,
    config: dict[str, str],
    target_ex5: Path,
) -> list[Path]:
    candidates: list[Path] = []
    for key in ("compiled_ex5_local_ex5", "compiled_ex5_local_path"):
        value = config.get(key, "")
        if not value:
            continue
        candidate = _resolve_config_path(project_root, value)
        if candidate.suffix.lower() != ".ex5" or not candidate.exists() or not candidate.is_file():
            continue
        if _same_file(candidate, target_ex5):
            candidates.append(candidate)
        elif _is_relative_to(candidate, project_root) and _git_ignored(candidate, project_root):
            candidates.append(candidate)
    return candidates


def _same_file(left: Path, right: Path) -> bool:
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return False


def _unique_existing(paths: list[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        try:
            key = str(path.resolve()).lower()
        except OSError:
            key = str(path).lower()
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return unique


def _metaeditor_path(project_root: Path) -> Path | None:
    _terminal, metaeditor = resolve_mt5_execution_paths(config_path=project_root / LOCAL_MT5_CONFIG_PATH)
    if not metaeditor:
        return None
    try:
        return validate_mt5_executable_path(metaeditor, "metaeditor64.exe")
    except (OSError, ValueError):
        return None


def _compile_with_metaeditor(
    *,
    metaeditor: Path,
    mq5_path: Path,
    private_log_path: Path,
    compile_runner: CompileRunner | None,
    timeout_seconds: int,
) -> tuple[bool, int | None]:
    private_log_path.parent.mkdir(parents=True, exist_ok=True)
    private_log_path.unlink(missing_ok=True)
    command = [str(metaeditor), f"/compile:{mq5_path}", f"/log:{private_log_path}"]
    runner: CompileRunner = compile_runner or subprocess.run
    completed = runner(
        command,
        cwd=mq5_path.parent,
        timeout=timeout_seconds,
        capture_output=True,
        text=True,
        check=False,
    )
    return (
        int(completed.returncode) == 0 or _compile_log_has_zero_errors(private_log_path),
        int(completed.returncode),
    )


def _compile_log_has_zero_errors(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return False
    return "result: 0 errors" in text


def _write_marker(
    project_root: Path,
    *,
    terminal_data_dir: Path,
    expert_relative_path: str,
    bootstrap_method: str,
) -> dict[str, object]:
    return write_compiled_ex5_readiness_marker(
        project_root,
        terminal_install_id=terminal_data_dir.name,
        terminal_fingerprint=terminal_data_dir.name,
        terminal_data_dir=terminal_data_dir,
        expert_relative_path=expert_relative_path,
        include_hash=False,
        bootstrap_method=bootstrap_method,
    )


def _sanitize_value(value: object) -> object:
    if isinstance(value, str):
        if _looks_like_path(value):
            return redact_public_path(value).replace(".ex5", "<COMPILED_EA_FILE>").replace(".mq5", "<MQL5_SOURCE_FILE>")
        return value
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_value(item) for key, item in value.items()}
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


def _sanitize_payload(payload: dict[str, object]) -> dict[str, object]:
    return {key: _sanitize_value(value) for key, value in payload.items()}


def build_compiled_ex5_terminal_bootstrap(
    project_root: Path,
    *,
    compile_runner: CompileRunner | None = None,
    allow_metaeditor_compile: bool = True,
    timeout_seconds: int = 120,
) -> dict[str, object]:
    config = _read_local_config(project_root)
    expert = normalize_expert_relative_path(config.get("expert_relative_path", DEFAULT_BOOTSTRAP_EXPERT))
    expert_validation = validate_expert_relative_path(expert)
    resolution = resolve_terminal_datadir(project_root)
    data_dir_found = bool(resolution.get("terminal_data_dir_found"))
    data_dir_text = str(resolution.get("terminal_data_dir", "") or "")
    data_dir = Path(data_dir_text) if data_dir_text else Path()
    target_ex5 = expected_ex5_path_in_terminal_datadir(data_dir, expert) if data_dir_text and expert else Path()
    target_mq5 = _expected_mq5_path(data_dir, expert) if data_dir_text and expert else Path()
    found_before = bool(target_ex5 and target_ex5.exists() and target_ex5.is_file())
    found_after = found_before
    marker_created = False
    marker_payload: dict[str, object] = {}
    bootstrap_method = METHOD_HOLD_MISSING
    status = HOLD_SOURCE_STATUS
    compiled_or_copied = False
    metaeditor_real_run = False
    metaeditor_exit_code: int | None = None
    blocking_issues: list[str] = [*list(resolution.get("blocking_issues", [])), *list(expert_validation["blocking_issues"])]
    warnings: list[str] = list(resolution.get("warnings", []))

    if not data_dir_found:
        status = HOLD_DATADIR_STATUS
        blocking_issues.append("terminal_data_dir_missing")
    elif not bool(expert_validation["expert_format_valid"]):
        status = HOLD_AMBIGUOUS_STATUS
    elif found_before:
        bootstrap_method = METHOD_ALREADY_PRESENT
        marker_payload = _write_marker(
            project_root,
            terminal_data_dir=data_dir,
            expert_relative_path=expert,
            bootstrap_method=bootstrap_method,
        )
        marker_created = True
        status = PASS_STATUS
    else:
        ex5_candidates = _unique_existing(_configured_ex5_candidates(project_root, config, target_ex5))
        mq5_candidates = _unique_existing(
            [
                *([target_mq5] if target_mq5.exists() and target_mq5.is_file() else []),
                *_safe_repo_mq5_candidates(project_root, expert),
                *_configured_mq5_candidates(project_root, config, target_mq5),
            ]
        )
        if len(ex5_candidates) > 1 or len(mq5_candidates) > 1:
            status = HOLD_AMBIGUOUS_STATUS
            bootstrap_method = METHOD_HOLD_AMBIGUOUS
            blocking_issues.append("expert_source_ambiguous")
        elif ex5_candidates:
            target_ex5.parent.mkdir(parents=True, exist_ok=True)
            if not _same_file(ex5_candidates[0], target_ex5):
                shutil.copy2(ex5_candidates[0], target_ex5)
                compiled_or_copied = True
            found_after = target_ex5.exists() and target_ex5.is_file()
            if found_after:
                bootstrap_method = METHOD_COPIED_EX5
                marker_payload = _write_marker(
                    project_root,
                    terminal_data_dir=data_dir,
                    expert_relative_path=expert,
                    bootstrap_method=bootstrap_method,
                )
                marker_created = True
                status = PASS_STATUS
        elif mq5_candidates:
            source_mq5 = mq5_candidates[0]
            target_mq5.parent.mkdir(parents=True, exist_ok=True)
            if not _same_file(source_mq5, target_mq5):
                shutil.copy2(source_mq5, target_mq5)
            metaeditor = _metaeditor_path(project_root) if allow_metaeditor_compile else None
            if not metaeditor:
                status = HOLD_METAEDITOR_STATUS
                blocking_issues.append("metaeditor_not_available_for_compile")
            else:
                metaeditor_real_run = True
                compile_ok, metaeditor_exit_code = _compile_with_metaeditor(
                    metaeditor=metaeditor,
                    mq5_path=target_mq5,
                    private_log_path=project_root
                    / "reports"
                    / "private"
                    / "local_readiness"
                    / "compiled_ex5_terminal_bootstrap_metaeditor.log",
                    compile_runner=compile_runner,
                    timeout_seconds=timeout_seconds,
                )
                found_after = target_ex5.exists() and target_ex5.is_file()
                if compile_ok and found_after:
                    compiled_or_copied = True
                    bootstrap_method = METHOD_COMPILED
                    marker_payload = _write_marker(
                        project_root,
                        terminal_data_dir=data_dir,
                        expert_relative_path=expert,
                        bootstrap_method=bootstrap_method,
                    )
                    marker_created = True
                    status = PASS_STATUS
                else:
                    status = HOLD_COMPILE_STATUS
                    blocking_issues.append("metaeditor_compile_failed_or_ex5_missing")
        else:
            blocking_issues.append("mql5_source_or_ex5_not_found")

    readiness = validate_compiled_ex5_readiness(
        project_root,
        environment={"terminal_data_dir": str(data_dir)} if data_dir else {},
        expert_relative_path=expert,
        readiness_marker=marker_payload if marker_created else {},
    )
    contract = build_terminal_contract_audit(project_root, environment={"terminal_data_dir": str(data_dir)} if data_dir else {})
    if status == PASS_STATUS and not bool(contract.get("ready_for_real_retry")):
        status = HOLD_COMPILE_STATUS
        blocking_issues.extend(list(contract.get("blocking_issues", [])))

    found_after = bool(target_ex5 and target_ex5.exists() and target_ex5.is_file())
    blocking_issues = list(dict.fromkeys(blocking_issues))
    if status == PASS_STATUS:
        blocking_issues = []
        next_step = "review/merge MVP-014K4, then operator may approve MVP-014L one-run real retry"
    elif "mql5_source_or_ex5_not_found" in blocking_issues:
        next_step = "provide or generate safe EA source before retry"
    elif status == HOLD_AMBIGUOUS_STATUS:
        next_step = "declare one safe expert source before retry"
    elif status == HOLD_METAEDITOR_STATUS:
        next_step = "configure MetaEditor path or provide compiled EX5 in ignored local config"
    elif status == HOLD_COMPILE_STATUS:
        next_step = "review controlled MetaEditor compile output before retry"
    else:
        next_step = "fix terminal DataDir EX5 bootstrap blockers before retry"

    payload = {
        "status": status,
        "datadir_source": str(resolution.get("datadir_source", "")),
        "terminal_data_dir_found": data_dir_found,
        "terminal_data_dir_structure_valid": bool(resolution.get("terminal_data_dir_structure_valid")),
        "bootstrap_command": "PASS" if status == PASS_STATUS else "HOLD",
        "bootstrap_method": bootstrap_method,
        "metaeditor_real_run": metaeditor_real_run,
        "metaeditor_exit_code": metaeditor_exit_code,
        "mt5_terminal_run": False,
        "compiled_ex5_found_before": found_before,
        "compiled_ex5_created_or_copied": compiled_or_copied,
        "compiled_ex5_found_after": found_after,
        "compiled_ex5_marker_created": marker_created,
        "compiled_ex5_verified_in_terminal_datadir": bool(
            readiness.get("compiled_ex5_verified_in_terminal_datadir")
        ),
        "terminal_datadir_consistent": bool(readiness.get("terminal_data_dir_consistent")),
        "expert_mapping_valid_for_tester": bool(readiness.get("expert_mapping_valid_for_strategy_tester")),
        "tester_ini_contract_ready": bool(contract.get("tester_ini_contract_ready")),
        "report_contract_ready": bool(contract.get("report_contract_ready")),
        "close_after_run_ready": bool(contract.get("close_after_run_ready")),
        "terminal_contract_audit": str(contract.get("terminal_contract_audit", "FAIL")),
        "real_mt5_preflight": "PASS" if status == PASS_STATUS and bool(contract.get("ready_for_real_retry")) else "HOLD",
        "real_mt5_runtime_dry_run": "PASS" if status == PASS_STATUS and bool(contract.get("ready_for_real_retry")) else "HOLD",
        "ready_for_real_retry": bool(status == PASS_STATUS and contract.get("ready_for_real_retry")),
        "blocking_issues": blocking_issues,
        "warnings": list(dict.fromkeys(warnings)),
        "datadir_resolution": public_datadir_resolution_summary(resolution),
        "readiness": {
            key: readiness.get(key)
            for key in (
                "compiled_ex5_verified_in_terminal_datadir",
                "terminal_data_dir_consistent",
                "expert_mapping_valid_for_strategy_tester",
                "blocking_issues",
                "warnings",
            )
        },
        "terminal_contract": {
            "terminal_contract_audit": contract.get("terminal_contract_audit", "FAIL"),
            "ready_for_real_retry": bool(contract.get("ready_for_real_retry")),
            "blocking_issues": list(contract.get("blocking_issues", [])),
        },
        "expert_relative_path": expert,
        "compiled_ex5_expected_path_sanitized": (
            redact_public_path(target_ex5).replace(".ex5", "<COMPILED_EA_FILE>") if target_ex5 else ""
        ),
        "compiled_mq5_expected_path_sanitized": (
            redact_public_path(target_mq5).replace(".mq5", "<MQL5_SOURCE_FILE>") if target_mq5 else ""
        ),
        "marker_path_sanitized": redact_public_path(marker_path(project_root)).replace(".json", "<JSON_MARKER>"),
        "marker_payload_created": bool(marker_payload),
        "created_at": _utc_now(),
        "next_mvp": "MVP-014L One-run Real Retry With Terminal Contract Audit PASS",
        "next_step": next_step,
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
    }
    return _sanitize_payload(payload)


def _markdown(payload: dict[str, object]) -> str:
    blocking = ", ".join(payload["blocking_issues"]) if payload["blocking_issues"] else "none"
    warnings = ", ".join(payload["warnings"]) if payload["warnings"] else "none"
    return "\n".join(
        [
            "# MVP-014K4 Safe Smoke EA Source and EX5 Bootstrap",
            "",
            "## 1. Executive Summary",
            "",
            f"- Status: {payload['status']}",
            f"- Bootstrap command: {payload['bootstrap_command']}",
            f"- Ready for MVP-014L: {str(payload['ready_for_real_retry']).lower()}",
            "",
            "## 2. Previous Blocker",
            "",
            "- MVP-014K3 resolved the terminal DataDir but did not find a safe source or EX5 to bootstrap.",
            "",
            "## 3. DataDir Source",
            "",
            f"- DataDir source: {payload['datadir_source']}",
            f"- Terminal DataDir found: {str(payload['terminal_data_dir_found']).lower()}",
            "",
            "## 4. Bootstrap Method",
            "",
            f"- Method: {payload['bootstrap_method']}",
            f"- MetaEditor real run: {str(payload['metaeditor_real_run']).lower()}",
            f"- MT5 terminal run: {str(payload['mt5_terminal_run']).lower()}",
            "",
            "## 5. EX5 Verification",
            "",
            f"- EX5 found before: {str(payload['compiled_ex5_found_before']).lower()}",
            f"- EX5 created or copied: {str(payload['compiled_ex5_created_or_copied']).lower()}",
            f"- EX5 found after: {str(payload['compiled_ex5_found_after']).lower()}",
            f"- Marker created: {str(payload['compiled_ex5_marker_created']).lower()}",
            f"- EX5 verified in terminal DataDir: {str(payload['compiled_ex5_verified_in_terminal_datadir']).lower()}",
            "",
            "## 6. Expert Mapping",
            "",
            f"- Expert mapping valid for tester: {str(payload['expert_mapping_valid_for_tester']).lower()}",
            f"- Terminal DataDir consistent: {str(payload['terminal_datadir_consistent']).lower()}",
            "",
            "## 7. Terminal Contract Audit Result",
            "",
            f"- Terminal contract audit: {payload['terminal_contract_audit']}",
            f"- Tester INI contract ready: {str(payload['tester_ini_contract_ready']).lower()}",
            f"- Report contract ready: {str(payload['report_contract_ready']).lower()}",
            f"- Close-after-run ready: {str(payload['close_after_run_ready']).lower()}",
            f"- Blocking issues: {blocking}",
            f"- Warnings: {warnings}",
            "",
            "## 8. Safety Boundary",
            "",
            "- MT5 real run new: false",
            "- Backtest real run new: false",
            "- Strategy Tester run new: false",
            "- EA executed new: false",
            "- Tournament 100 run: false",
            "- Credentials stored: false",
            "- Private files committed: false",
            "- EX5 committed: false",
            "- SET committed: false",
            "- Paths sanitized: true",
            "",
            "## 9. Readiness for MVP-014L",
            "",
            f"- Next MVP: {payload['next_mvp']}",
            f"- Next step: {payload['next_step']}",
        ]
    ) + "\n"


def generate_compiled_ex5_terminal_bootstrap(project_root: Path) -> dict[str, object]:
    payload = build_compiled_ex5_terminal_bootstrap(project_root)
    public_json = project_root / PUBLIC_TERMINAL_BOOTSTRAP_JSON
    public_md = project_root / PUBLIC_TERMINAL_BOOTSTRAP_MD
    public_safe_json = project_root / PUBLIC_SAFE_SMOKE_BOOTSTRAP_JSON
    public_safe_md = project_root / PUBLIC_SAFE_SMOKE_BOOTSTRAP_MD
    public_report = project_root / PUBLIC_TERMINAL_BOOTSTRAP_REPORT
    public_json.parent.mkdir(parents=True, exist_ok=True)
    public_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown = _markdown(payload)
    public_md.write_text(markdown, encoding="utf-8")
    public_safe_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    public_safe_md.write_text(markdown, encoding="utf-8")
    public_report.write_text(markdown, encoding="utf-8")
    return {
        "status": payload["status"],
        "summary": payload,
        "files": {
            "json": str(public_json),
            "markdown": str(public_md),
            "safe_smoke_json": str(public_safe_json),
            "safe_smoke_markdown": str(public_safe_md),
            "report": str(public_report),
        },
    }
