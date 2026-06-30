"""Terminal DataDir and Strategy Tester contract audit.

The audit is non-executing: it does not launch MT5, MetaEditor, Strategy Tester,
compile an EX5, or run an EA. It checks whether local metadata proves that the
compiled EA is available inside the terminal DataDir and that tester.ini can
refer to it with a Strategy Tester compatible Expert value.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.core.compiled_ex5_readiness import (
    DEFAULT_BOOTSTRAP_EXPERT,
    load_compiled_ex5_readiness_marker,
    public_readiness_summary,
    validate_compiled_ex5_readiness,
    validate_expert_relative_path,
)
from app.core.mt5_datadir_resolver import public_datadir_resolution_summary, resolve_terminal_datadir
from app.core.mt5_detection import build_local_mt5_environment_status, redact_public_path
from app.core.strategy_tester_report_config import (
    build_strategy_tester_report_contract,
    build_tester_ini_report_lines,
)


PUBLIC_TERMINAL_CONTRACT_JSON = Path("reports") / "public" / "terminal_contract_audit_summary.json"
PUBLIC_TERMINAL_CONTRACT_MD = Path("reports") / "public" / "terminal_contract_audit_summary.md"
PUBLIC_TERMINAL_CONTRACT_REPORT = (
    Path("reports") / "public" / "MVP_014K_TERMINAL_DATADIR_EX5_VERIFICATION_REPORT.md"
)
DEFAULT_EXPERT = DEFAULT_BOOTSTRAP_EXPERT

PASS_STATUS = "PASS_MVP_014K_TERMINAL_DATADIR_EX5_VERIFICATION_COMPLETED"
HOLD_STATUS = "HOLD_MVP_014K_TERMINAL_CONTRACT_BLOCKED"


def _parse_tester_ini(tester_ini_text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in tester_ini_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";") or line.startswith("#"):
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


def _build_tester_ini(expert: str, symbol: str, timeframe: str, report_contract: dict[str, object]) -> str:
    return "\n".join(
        [
            "[Tester]",
            f"Expert={expert}",
            f"Symbol={symbol}",
            f"Period={timeframe}",
            "Model=0",
            "Optimization=0",
            "Deposit=10000",
            "Currency=USD",
            *build_tester_ini_report_lines(report_contract),
            "",
        ]
    )


def validate_tester_ini_terminal_contract(
    tester_ini_text: str,
    *,
    readiness: dict[str, object],
    symbol: str = "XAUUSD",
    timeframe: str = "M5",
) -> dict[str, object]:
    values = _parse_tester_ini(tester_ini_text)
    expert = values.get("Expert", "")
    expert_validation = validate_expert_relative_path(expert)
    issues: list[str] = []
    if values.get("_section") != "Tester":
        issues.append("tester_section_missing")
    if not expert:
        issues.append("expert_missing")
    issues.extend(str(item) for item in expert_validation["blocking_issues"])
    if values.get("Symbol") != symbol:
        issues.append("symbol_mismatch")
    if values.get("Period") != timeframe:
        issues.append("timeframe_mismatch")
    if values.get("Optimization") != "0":
        issues.append("optimization_must_be_zero")
    if not values.get("Report"):
        issues.append("report_missing")
    elif not _is_private_report_path(values["Report"]):
        issues.append("report_path_not_private")
    if values.get("ReplaceReport") != "1":
        issues.append("replace_report_required")
    if values.get("ShutdownTerminal") != "1":
        issues.append("shutdown_terminal_required")
    if not bool(readiness.get("expert_mapping_valid_for_strategy_tester")):
        issues.append("expert_mapping_invalid_for_strategy_tester")
    return {
        "tester_ini_contract_ready": not issues,
        "expert_mapping_valid_for_strategy_tester": bool(readiness.get("expert_mapping_valid_for_strategy_tester")),
        "expert_parameters_status": str(readiness.get("expert_parameters_status", "")),
        "blocking_issues": list(dict.fromkeys(issues)),
        "tester_ini_values": {
            "section": values.get("_section", ""),
            "expert_set": bool(values.get("Expert")),
            "symbol": values.get("Symbol", ""),
            "timeframe": values.get("Period", ""),
            "optimization": values.get("Optimization", ""),
            "report_configured": bool(values.get("Report")),
            "replace_report": values.get("ReplaceReport", ""),
            "shutdown_terminal": values.get("ShutdownTerminal", ""),
        },
    }


def _validate_report_contract(report_contract: dict[str, object]) -> dict[str, object]:
    issues: list[str] = []
    if not bool(report_contract.get("report_export_configured")):
        issues.append("report_export_not_configured")
    if not bool(report_contract.get("replace_report")):
        issues.append("replace_report_not_enabled")
    if not bool(report_contract.get("shutdown_terminal")):
        issues.append("shutdown_terminal_not_enabled")
    for key in ("report_base", "private_run_dir", "private_mt5_staging_dir", "expected_log_dir"):
        value = str(report_contract.get(key, "") or "")
        if not value or not _is_private_report_path(value):
            issues.append(f"{key}_not_private")
    expected = report_contract.get("expected_report_paths", [])
    if not isinstance(expected, list) or not expected:
        issues.append("expected_report_paths_missing")
    elif not all(isinstance(item, str) and _is_private_report_path(item) for item in expected):
        issues.append("expected_report_paths_not_private")
    return {
        "report_contract_ready": not issues,
        "close_after_run_ready": bool(report_contract.get("shutdown_terminal")),
        "blocking_issues": list(dict.fromkeys(issues)),
    }


def _sanitize_public_value(value: object) -> object:
    if isinstance(value, str):
        if not _looks_like_path(value):
            return value
        sanitized = redact_public_path(value)
        sanitized = re.sub(r"(?i)\.ex5\b", "<COMPILED_EA_FILE>", sanitized)
        sanitized = re.sub(r"(?i)\.set\b", "<SET_FILE>", sanitized)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_public_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_public_value(item) for key, item in value.items()}
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


def sanitize_terminal_contract_summary(payload: dict[str, object]) -> dict[str, object]:
    return {key: _sanitize_public_value(value) for key, value in payload.items()}


def build_terminal_contract_audit(
    project_root: Path,
    *,
    environment: dict[str, object] | None = None,
    expert: str = DEFAULT_EXPERT,
    symbol: str = "XAUUSD",
    timeframe: str = "M5",
    tester_ini_text: str | None = None,
    report_contract: dict[str, object] | None = None,
    readiness_marker: dict[str, object] | None = None,
    allow_external_filesystem_check: bool = False,
    resolve_datadir: bool = True,
) -> dict[str, object]:
    marker = readiness_marker if readiness_marker is not None else load_compiled_ex5_readiness_marker(project_root)
    datadir_resolution: dict[str, object] = {}
    env = dict(environment) if environment is not None else build_local_mt5_environment_status()
    if marker.get("terminal_data_dir"):
        datadir_resolution = {
            "terminal_data_dir_found": True,
            "terminal_data_dir_sanitized": redact_public_path(str(marker.get("terminal_data_dir", ""))),
            "datadir_source": "compiled_ex5_readiness_marker",
            "terminal_data_dir_structure_valid": True,
            "mql5_dir_found": True,
            "experts_dir_found": True,
            "tester_profiles_dir_found": False,
            "terminal_path_sanitized": "",
            "origin_txt_found": False,
            "origin_txt_matched_terminal": False,
            "blocking_issues": [],
            "warnings": [],
        }
    elif resolve_datadir and not env.get("terminal_data_dir"):
        datadir_resolution = resolve_terminal_datadir(project_root)
        if datadir_resolution.get("terminal_data_dir_found"):
            env["terminal_data_dir"] = str(datadir_resolution.get("terminal_data_dir", ""))
    report = report_contract or build_strategy_tester_report_contract("mvp_014k_terminal_contract_audit")
    tester_text = tester_ini_text or _build_tester_ini(expert, symbol, timeframe, report)
    values = _parse_tester_ini(tester_text)
    configured_expert = values.get("Expert", expert)
    readiness = validate_compiled_ex5_readiness(
        project_root,
        environment=env,
        expert_relative_path=configured_expert,
        readiness_marker=marker,
        expert_parameters=values.get("ExpertParameters", ""),
        expert_parameters_required=False,
        allow_external_filesystem_check=allow_external_filesystem_check,
    )
    tester = validate_tester_ini_terminal_contract(
        tester_text,
        readiness=readiness,
        symbol=symbol,
        timeframe=timeframe,
    )
    report_result = _validate_report_contract(report)
    blocking_issues = list(
        dict.fromkeys(
            [
                *list(readiness.get("blocking_issues", [])),
                *list(tester["blocking_issues"]),
                *list(report_result["blocking_issues"]),
            ]
        )
    )
    ready = bool(
        not blocking_issues
        and readiness.get("compiled_ex5_verified_in_terminal_datadir")
        and readiness.get("terminal_data_dir_consistent")
        and tester.get("expert_mapping_valid_for_strategy_tester")
        and tester.get("tester_ini_contract_ready")
        and report_result.get("report_contract_ready")
        and report_result.get("close_after_run_ready")
    )
    if ready:
        next_step = "operator may approve MVP-014L one-run real retry only if terminal contract audit remains PASS"
    elif "terminal_data_dir_missing" in blocking_issues:
        next_step = "configure terminal_data_dir in ignored local config before retry"
    elif "compiled_ex5_not_found_in_terminal_datadir" in blocking_issues:
        next_step = "compile_or_copy_ex5_to_terminal_datadir_before_retry"
    else:
        next_step = "fix terminal contract blocking issues before any real retry"
    payload = {
        "status": PASS_STATUS if ready else HOLD_STATUS,
        "terminal_contract_audit": "PASS" if ready else "FAIL",
        "terminal_contract_audit_command": True,
        "terminal_data_dir_found": bool(readiness.get("terminal_data_dir_recorded")),
        "datadir_source": str(datadir_resolution.get("datadir_source", "")),
        "datadir_resolution": public_datadir_resolution_summary(datadir_resolution) if datadir_resolution else {},
        "compiled_ex5_verified_in_terminal_datadir": bool(
            readiness.get("compiled_ex5_verified_in_terminal_datadir")
        ),
        "terminal_datadir_consistent": bool(readiness.get("terminal_data_dir_consistent")),
        "expert_mapping_valid_for_tester": bool(tester.get("expert_mapping_valid_for_strategy_tester")),
        "expert_parameters_status": str(readiness.get("expert_parameters_status", "")),
        "tester_ini_contract_ready": bool(tester.get("tester_ini_contract_ready")),
        "report_contract_ready": bool(report_result.get("report_contract_ready")),
        "close_after_run_ready": bool(report_result.get("close_after_run_ready")),
        "ready_for_real_retry": ready,
        "blocking_issues": blocking_issues,
        "warnings": list(readiness.get("warnings", [])),
        "readiness": public_readiness_summary(readiness),
        "tester_ini_contract": tester["tester_ini_values"],
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
    return sanitize_terminal_contract_summary(payload)


def _terminal_contract_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# MVP-014K Terminal DataDir EX5 Verification",
        "",
        f"- Status: {payload['status']}",
        f"- Terminal contract audit: {payload['terminal_contract_audit']}",
        f"- Terminal DataDir found: {str(payload['terminal_data_dir_found']).lower()}",
        f"- DataDir source: {payload['datadir_source'] or 'not_found'}",
        f"- Compiled EX5 verified in terminal DataDir: {str(payload['compiled_ex5_verified_in_terminal_datadir']).lower()}",
        f"- Terminal DataDir consistent: {str(payload['terminal_datadir_consistent']).lower()}",
        f"- Expert mapping valid for tester: {str(payload['expert_mapping_valid_for_tester']).lower()}",
        f"- Expert parameters status: {payload['expert_parameters_status']}",
        f"- Tester INI contract ready: {str(payload['tester_ini_contract_ready']).lower()}",
        f"- Report contract ready: {str(payload['report_contract_ready']).lower()}",
        f"- Close-after-run ready: {str(payload['close_after_run_ready']).lower()}",
        f"- Ready for real retry: {str(payload['ready_for_real_retry']).lower()}",
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
        "This audit is non-executing. It does not launch MT5, MetaEditor, Strategy Tester, compile an EX5 or execute an EA.",
    ]
    return "\n".join(lines) + "\n"


def generate_terminal_contract_audit(project_root: Path) -> dict[str, object]:
    payload = build_terminal_contract_audit(project_root)
    public_json = project_root / PUBLIC_TERMINAL_CONTRACT_JSON
    public_md = project_root / PUBLIC_TERMINAL_CONTRACT_MD
    public_report = project_root / PUBLIC_TERMINAL_CONTRACT_REPORT
    public_json.parent.mkdir(parents=True, exist_ok=True)
    public_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown = _terminal_contract_markdown(payload)
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
