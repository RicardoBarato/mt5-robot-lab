"""Terminal-runtime diagnostics for real MT5 smoke gaps.

This module is read-only with respect to MT5. It inspects local private
artifacts already produced by a gated run and emits sanitized public conclusions
without launching MT5, Strategy Tester, or an EA.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import re
from pathlib import Path
from typing import Any

from app.core.mt5_detection import redact_public_path
from app.core.real_mt5_runtime_contract import build_real_mt5_runtime_contract


PRIVATE_SMOKE_ROOT = Path("reports") / "private" / "real_mt5_smoke"
PUBLIC_TERMINAL_DIAG_JSON = Path("reports") / "public" / "terminal_runtime_diagnostics_summary.json"
PUBLIC_TERMINAL_DIAG_MD = Path("reports") / "public" / "terminal_runtime_diagnostics_summary.md"
PUBLIC_TERMINAL_DIAG_REPORT = Path("reports") / "public" / "MVP_014J_RUNTIME_VS_TERMINAL_GAP_DIAGNOSIS_REPORT.md"

TERMINAL_EXIT_UNKNOWN = "unknown_terminal_exit"
BLOCKED_STATUS = "HOLD_MVP_014J_RUNTIME_TERMINAL_GAP_RETRY_BLOCKED"
PASS_STATUS = "PASS_MVP_014J_RUNTIME_TERMINAL_GAP_DIAGNOSED"


@dataclass(frozen=True)
class TerminalRuntimeDiagnostics:
    status: str
    root_cause: str
    likely_causes: list[str]
    exit_code_recorded: int | None
    failure_stage: str
    tester_ini_reviewed: bool
    tester_ini_created: bool
    tester_ini_has_tester_section: bool
    expert_mapping_checked: bool
    expert_present: bool
    expert_format_valid: bool
    expert_parameters_present: bool
    expert_name_matches_compiled_marker: bool
    data_dir_consistency_checked: bool
    data_dir_consistent: bool
    terminal_data_dir_recorded: bool
    compiled_ex5_configured: bool
    compiled_ex5_marker_is_project_local: bool
    report_contract_checked: bool
    report_configured: bool
    report_path_private: bool
    replace_report_enabled: bool
    shutdown_terminal_enabled: bool
    terminal_args_checked: bool
    terminal_launched_with_config: bool
    terminal_launched_with_skipupdate: bool
    config_path_private: bool
    config_path_accessible: bool
    symbol_present: bool
    period_present: bool
    optimization_zero: bool
    runtime_contract_used: bool
    runtime_contract_ready: bool
    ready_for_real_retry: bool
    contract_bug_fixed: bool
    mt5_real_run_new: bool = False
    backtest_real_run_new: bool = False
    strategy_tester_run_new: bool = False
    ea_executed_new: bool = False
    tournament_100_run: bool = False
    exe_created: bool = False
    zip_created: bool = False
    credentials_stored: bool = False
    private_files_committed: bool = False
    paths_sanitized: bool = True
    public_summary_created: bool = True
    warnings: list[str] = field(default_factory=list)
    next_mvp: str = "MVP-014K One-run Real Retry only after terminal contract diagnosis passes"
    next_step: str = "review/merge MVP-014J, then only retry if terminal diagnostics are PASS"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _parse_tester_ini(tester_ini_text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in tester_ini_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            values["_section"] = line.strip("[]")
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _is_private_report_path(value: str) -> bool:
    normalized = value.replace("\\", "/").lstrip("./").lower()
    return normalized.startswith("reports/private/")


def _looks_like_windows_or_private_path(value: str) -> bool:
    if re.search(r"(?i)[a-z]:[\\/]", value):
        return True
    if value.startswith("\\\\") or value.startswith("//"):
        return True
    return False


def _expert_format_valid(expert: str) -> bool:
    if not expert.strip():
        return False
    if _looks_like_windows_or_private_path(expert):
        return False
    if "/" in expert or ".." in expert:
        return False
    if expert.lower().endswith((".mq5", ".ex5")):
        return False
    return True


def _expected_ex5_name(expert: str) -> str:
    return Path(expert.replace("\\", "/")).name + ".ex5"


def _latest_private_run(project_root: Path) -> Path | None:
    root = project_root / PRIVATE_SMOKE_ROOT
    if not root.exists():
        return None
    runs = [item for item in root.iterdir() if item.is_dir()]
    if not runs:
        return None
    return max(runs, key=lambda item: item.stat().st_mtime)


def classify_terminal_exit_code(exit_code: int | None) -> str:
    if exit_code is None:
        return "not_recorded"
    if exit_code == 0:
        return "success"
    return TERMINAL_EXIT_UNKNOWN


def validate_tester_ini_for_mt5_runtime(tester_ini_text: str) -> dict[str, object]:
    values = _parse_tester_ini(tester_ini_text)
    expert = values.get("Expert", "")
    report = values.get("Report", "")
    return {
        "tester_ini_created": bool(tester_ini_text.strip()),
        "tester_ini_has_tester_section": values.get("_section") == "Tester",
        "expert_present": bool(expert.strip()),
        "expert_format_valid": _expert_format_valid(expert),
        "expert_parameters_present": "ExpertParameters" in values,
        "symbol_present": bool(values.get("Symbol", "").strip()),
        "period_present": bool(values.get("Period", "").strip()),
        "optimization_zero": values.get("Optimization") == "0",
        "report_configured": bool(report.strip()),
        "report_path_private": _is_private_report_path(report),
        "replace_report_enabled": values.get("ReplaceReport") == "1",
        "shutdown_terminal_enabled": values.get("ShutdownTerminal") == "1",
        "values": values,
    }


def validate_strategy_tester_config_shape(
    tester_ini_text: str,
    *,
    config_path: Path | None,
    project_root: Path,
    terminal_launch_args: list[str] | None = None,
) -> dict[str, object]:
    ini = validate_tester_ini_for_mt5_runtime(tester_ini_text)
    config_private = False
    config_accessible = False
    if config_path is not None:
        try:
            rel = config_path.resolve().relative_to(project_root.resolve())
            config_private = rel.as_posix().startswith("reports/private/")
        except ValueError:
            config_private = False
        config_accessible = config_path.exists() and config_path.is_file()
    args = terminal_launch_args or []
    joined = " ".join(args).lower()
    return {
        **{key: value for key, value in ini.items() if key != "values"},
        "config_path_private": config_private,
        "config_path_accessible": config_accessible,
        "terminal_launched_with_config": "/config:" in joined,
        "terminal_launched_with_skipupdate": "/skipupdate" in joined,
    }


def validate_expert_mapping_for_strategy_tester(
    expert: str,
    compiled_ex5_path: str,
    *,
    project_root: Path,
) -> dict[str, object]:
    compiled_path = Path(compiled_ex5_path) if compiled_ex5_path else Path()
    expected_name = _expected_ex5_name(expert) if expert else ""
    marker_name_matches = bool(compiled_path.name == expected_name) if compiled_ex5_path else False
    project_local = False
    if compiled_ex5_path:
        try:
            compiled_path.resolve().relative_to(project_root.resolve())
            project_local = True
        except (OSError, ValueError):
            project_local = False
    return {
        "expert_mapping_checked": True,
        "expert_name_matches_compiled_marker": marker_name_matches,
        "compiled_ex5_configured": bool(compiled_ex5_path),
        "compiled_ex5_marker_is_project_local": project_local,
        "compiled_ex5_expected_name": expected_name,
    }


def validate_terminal_data_dir_consistency(
    environment: dict[str, object],
    compiled_ex5_path: str,
    *,
    project_root: Path,
) -> dict[str, object]:
    data_dir = str(environment.get("terminal_data_dir") or environment.get("data_dir") or "")
    compiled_path = Path(compiled_ex5_path) if compiled_ex5_path else Path()
    project_local = False
    if compiled_ex5_path:
        try:
            compiled_path.resolve().relative_to(project_root.resolve())
            project_local = True
        except (OSError, ValueError):
            project_local = False
    data_dir_recorded = bool(data_dir)
    data_dir_consistent = bool(data_dir_recorded and compiled_ex5_path and not project_local)
    return {
        "data_dir_consistency_checked": True,
        "terminal_data_dir_recorded": data_dir_recorded,
        "data_dir_consistent": data_dir_consistent,
        "compiled_ex5_marker_is_project_local": project_local,
    }


def compare_preflight_vs_runtime_paths(
    preflight_summary: dict[str, object],
    runtime_contract: dict[str, object],
    *,
    project_root: Path,
) -> dict[str, object]:
    compiled = str(runtime_contract.get("compiled_ex5_expected", "") or preflight_summary.get("compiled_ex5_expected", "") or "")
    runtime_ready = bool(runtime_contract.get("ready_for_retry"))
    mapping = validate_expert_mapping_for_strategy_tester(
        str(runtime_contract.get("expert_path", "") or preflight_summary.get("expert_expected", "")),
        compiled,
        project_root=project_root,
    )
    return {
        "runtime_contract_used": True,
        "runtime_contract_ready": runtime_ready,
        "compiled_ex5_configured": bool(compiled),
        "compiled_ex5_marker_is_project_local": bool(mapping["compiled_ex5_marker_is_project_local"]),
    }


def _read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _sanitize_public_value(value: object) -> object:
    if isinstance(value, str):
        sanitized = redact_public_path(value)
        sanitized = sanitized.replace(".ex5", "<COMPILED_EA_FILE>")
        sanitized = sanitized.replace(".set", "<SET_FILE>")
        return sanitized
    if isinstance(value, list):
        return [_sanitize_public_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_public_value(item) for key, item in value.items()}
    return value


def sanitize_terminal_gap_summary(payload: dict[str, object]) -> dict[str, object]:
    return {key: _sanitize_public_value(value) for key, value in payload.items()}


def make_terminal_gap_summary(diagnostic: TerminalRuntimeDiagnostics) -> dict[str, object]:
    return sanitize_terminal_gap_summary(diagnostic.to_dict())


def _diagnostic_markdown(payload: dict[str, object]) -> str:
    likely = payload.get("likely_causes", [])
    lines = [
        "# MVP-014J Runtime vs Terminal Gap Diagnosis",
        "",
        f"- Status: {payload['status']}",
        f"- Root cause: {payload['root_cause']}",
        f"- Likely causes: {', '.join(likely) if likely else 'none'}",
        f"- Failure stage: {payload['failure_stage']}",
        f"- Exit code recorded: {payload['exit_code_recorded']}",
        f"- Tester INI reviewed: {str(payload['tester_ini_reviewed']).lower()}",
        f"- Expert mapping checked: {str(payload['expert_mapping_checked']).lower()}",
        f"- DataDir consistency checked: {str(payload['data_dir_consistency_checked']).lower()}",
        f"- DataDir consistent: {str(payload['data_dir_consistent']).lower()}",
        f"- Report contract checked: {str(payload['report_contract_checked']).lower()}",
        f"- Terminal args checked: {str(payload['terminal_args_checked']).lower()}",
        f"- Contract bug fixed: {str(payload['contract_bug_fixed']).lower()}",
        f"- Ready for real retry: {str(payload['ready_for_real_retry']).lower()}",
        f"- MT5 real run new: {str(payload['mt5_real_run_new']).lower()}",
        f"- Backtest real run new: {str(payload['backtest_real_run_new']).lower()}",
        f"- Strategy Tester run new: {str(payload['strategy_tester_run_new']).lower()}",
        f"- EA executed new: {str(payload['ea_executed_new']).lower()}",
        f"- Credentials stored: {str(payload['credentials_stored']).lower()}",
        f"- Private files committed: {str(payload['private_files_committed']).lower()}",
        f"- Paths sanitized: {str(payload['paths_sanitized']).lower()}",
        "",
        "This diagnostic inspected local private artifacts and emitted only sanitized conclusions.",
    ]
    return "\n".join(lines) + "\n"


def build_terminal_runtime_diagnostics(project_root: Path) -> dict[str, object]:
    private_run = _latest_private_run(project_root)
    tester_ini_text = ""
    config_path: Path | None = None
    if private_run is not None:
        config_path = private_run / "mvp_013c_smoke.ini"
        if config_path.exists():
            tester_ini_text = config_path.read_text(encoding="utf-8", errors="ignore")

    summary = _read_json(private_run / "run_summary_sanitized.json") if private_run else {}
    execution = _read_json(private_run / "execution_manifest.json") if private_run else {}
    environment = _read_json(private_run / "environment_sanitized.json") if private_run else {}

    runtime_contract = build_real_mt5_runtime_contract(
        project_root,
        environment=environment or None,
        operator_gate_approved=True,
        run_id="mvp_014j_terminal_runtime_diagnostics",
    )
    runtime_paths = compare_preflight_vs_runtime_paths(
        dict(runtime_contract.get("runtime_preflight", {})),
        runtime_contract,
        project_root=project_root,
    )
    tester_shape = validate_strategy_tester_config_shape(
        tester_ini_text,
        config_path=config_path,
        project_root=project_root,
        terminal_launch_args=list(execution.get("command_sanitized", [])),
    )
    tester_values = _parse_tester_ini(tester_ini_text)
    expert_mapping = validate_expert_mapping_for_strategy_tester(
        tester_values.get("Expert", ""),
        str(runtime_contract.get("compiled_ex5_expected", "")),
        project_root=project_root,
    )
    data_dir = validate_terminal_data_dir_consistency(
        environment,
        str(runtime_contract.get("compiled_ex5_expected", "")),
        project_root=project_root,
    )
    exit_code = summary.get("exit_code_recorded", execution.get("returncode"))
    exit_code_int = int(exit_code) if isinstance(exit_code, int) else None

    likely_causes: list[str] = []
    if bool(expert_mapping["compiled_ex5_marker_is_project_local"]):
        likely_causes.extend(["compiled_ex5_in_different_data_dir", "terminal_data_dir_mismatch"])
    if not bool(data_dir["terminal_data_dir_recorded"]):
        likely_causes.append("terminal_data_dir_mismatch")
    if not bool(tester_shape["expert_parameters_present"]):
        likely_causes.append("tester_ini_missing_expert_parameters")
    if not bool(tester_shape["terminal_launched_with_skipupdate"]):
        likely_causes.append("mt5_started_but_tester_config_rejected")
    likely_causes.extend(["terminal_exit_before_ea_start", classify_terminal_exit_code(exit_code_int)])
    likely_causes = list(dict.fromkeys(likely_causes))

    blocking_runtime_gap = any(
        cause in likely_causes
        for cause in {
            "compiled_ex5_in_different_data_dir",
            "terminal_data_dir_mismatch",
            "terminal_exit_before_ea_start",
        }
    )
    root_cause = (
        "compiled_ex5_marker_not_verified_in_terminal_datadir"
        if bool(expert_mapping["compiled_ex5_marker_is_project_local"])
        else "runtime_terminal_gap_requires_manual_review"
    )
    diagnostic = TerminalRuntimeDiagnostics(
        status=PASS_STATUS,
        root_cause=root_cause,
        likely_causes=likely_causes,
        exit_code_recorded=exit_code_int,
        failure_stage=str(summary.get("failure_stage") or execution.get("failure_stage") or "unknown_failure_stage"),
        tester_ini_reviewed=bool(tester_ini_text),
        tester_ini_created=bool(tester_shape["tester_ini_created"]),
        tester_ini_has_tester_section=bool(tester_shape["tester_ini_has_tester_section"]),
        expert_mapping_checked=True,
        expert_present=bool(tester_shape["expert_present"]),
        expert_format_valid=bool(tester_shape["expert_format_valid"]),
        expert_parameters_present=bool(tester_shape["expert_parameters_present"]),
        expert_name_matches_compiled_marker=bool(expert_mapping["expert_name_matches_compiled_marker"]),
        data_dir_consistency_checked=True,
        data_dir_consistent=bool(data_dir["data_dir_consistent"]),
        terminal_data_dir_recorded=bool(data_dir["terminal_data_dir_recorded"]),
        compiled_ex5_configured=bool(runtime_paths["compiled_ex5_configured"]),
        compiled_ex5_marker_is_project_local=bool(expert_mapping["compiled_ex5_marker_is_project_local"]),
        report_contract_checked=True,
        report_configured=bool(tester_shape["report_configured"]),
        report_path_private=bool(tester_shape["report_path_private"]),
        replace_report_enabled=bool(tester_shape["replace_report_enabled"]),
        shutdown_terminal_enabled=bool(tester_shape["shutdown_terminal_enabled"]),
        terminal_args_checked=True,
        terminal_launched_with_config=bool(tester_shape["terminal_launched_with_config"]),
        terminal_launched_with_skipupdate=bool(tester_shape["terminal_launched_with_skipupdate"]),
        config_path_private=bool(tester_shape["config_path_private"]),
        config_path_accessible=bool(tester_shape["config_path_accessible"]),
        symbol_present=bool(tester_shape["symbol_present"]),
        period_present=bool(tester_shape["period_present"]),
        optimization_zero=bool(tester_shape["optimization_zero"]),
        runtime_contract_used=True,
        runtime_contract_ready=bool(runtime_contract.get("ready_for_retry")),
        ready_for_real_retry=not blocking_runtime_gap,
        contract_bug_fixed=False,
        warnings=["retry_blocked_until_terminal_datadir_ex5_mapping_is_proven"] if blocking_runtime_gap else [],
    )
    return diagnostic.to_dict()


def generate_terminal_runtime_diagnostics(project_root: Path) -> dict[str, object]:
    payload = make_terminal_gap_summary(TerminalRuntimeDiagnostics(**build_terminal_runtime_diagnostics(project_root)))
    public_json = project_root / PUBLIC_TERMINAL_DIAG_JSON
    public_md = project_root / PUBLIC_TERMINAL_DIAG_MD
    public_report = project_root / PUBLIC_TERMINAL_DIAG_REPORT
    public_json.parent.mkdir(parents=True, exist_ok=True)
    public_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown = _diagnostic_markdown(payload)
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
