"""Runtime contract for a gated real MT5 smoke retry.

This module is intentionally non-executing. It bridges the preflight readiness
marker into the runtime preflight config so the real runner and the dry-run use
the same contract before any terminal launch is allowed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import time
from pathlib import Path
from typing import Any

from app.core.compiled_ex5_readiness import (
    load_compiled_ex5_readiness_marker,
    public_readiness_summary,
    validate_compiled_ex5_readiness,
)
from app.core.mt5_detection import build_local_mt5_environment_status, redact_public_path
from app.core.real_mt5_preflight import (
    DEFAULT_EXPERT,
    RealMT5PreflightConfig,
    build_real_mt5_preflight_check,
    expected_preflight_ex5_marker_path,
)
from app.core.strategy_tester_report_config import (
    build_strategy_tester_report_contract,
    build_tester_ini_report_lines,
)
from app.core.terminal_contract_audit import build_terminal_contract_audit


PUBLIC_RUNTIME_DRY_RUN_JSON = Path("reports") / "public" / "real_mt5_runtime_dry_run_summary.json"
PUBLIC_RUNTIME_DRY_RUN_MD = Path("reports") / "public" / "real_mt5_runtime_dry_run_summary.md"
PUBLIC_RUNTIME_DRY_RUN_REPORT = Path("reports") / "public" / "MVP_014H_RUNTIME_PREFLIGHT_MARKER_HANDOFF_REPORT.md"
DEFAULT_MARKER_MAX_AGE_SECONDS = 7 * 24 * 60 * 60


@dataclass(frozen=True)
class RealMT5RuntimeContract:
    operator_gate_approved: bool
    ready_for_retry: bool
    ex5_readiness_marker_present: bool
    ex5_readiness_marker_stale: bool
    compiled_ex5_configured: bool
    compiled_ex5_expected: str
    expert_path: str
    symbol: str
    timeframe: str
    max_backtests: int
    smoke_only: bool
    close_after_run_policy: str
    tournament_100_run: bool
    credentials_stored: bool
    tester_ini_contract: dict[str, object]
    report_contract: dict[str, object]
    runtime_preflight: dict[str, object]
    root_cause: str
    terminal_contract_audit_required: bool
    compiled_ex5_verified_in_terminal_datadir: bool
    terminal_datadir_consistent: bool
    expert_mapping_valid_for_tester: bool
    blocking_issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


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


def _is_marker_stale(marker_path: Path, max_age_seconds: int) -> bool:
    if max_age_seconds <= 0:
        return False
    age_seconds = time.time() - marker_path.stat().st_mtime
    return age_seconds > max_age_seconds


def _sanitize_public_value(value: object) -> object:
    if isinstance(value, str):
        return redact_public_path(value).replace(".ex5", "<COMPILED_EA_FILE>")
    if isinstance(value, list):
        return [_sanitize_public_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_public_value(item) for key, item in value.items()}
    return value


def sanitize_runtime_contract_summary(payload: dict[str, object]) -> dict[str, object]:
    return {key: _sanitize_public_value(value) for key, value in payload.items()}


def attach_ex5_readiness_to_runtime_contract(
    project_root: Path,
    contract: dict[str, object],
    *,
    marker_path: Path | None = None,
    marker_max_age_seconds: int = DEFAULT_MARKER_MAX_AGE_SECONDS,
) -> dict[str, object]:
    marker = marker_path or expected_preflight_ex5_marker_path(project_root)
    readiness_marker = load_compiled_ex5_readiness_marker(project_root)
    updated = dict(contract)
    updated["ex5_readiness_marker_present"] = marker.exists() and marker.is_file()
    updated["ex5_readiness_marker_stale"] = False
    updated["compiled_ex5_expected"] = ""
    updated["compiled_ex5_configured"] = False
    updated["ex5_marker_issue"] = ""

    marker_expected = Path(str(readiness_marker.get("compiled_ex5_expected_path", "") or ""))
    if marker_expected.suffix.lower() == ".ex5" and marker_expected.exists() and marker_expected.is_file():
        updated["ex5_readiness_marker_present"] = True
        updated["compiled_ex5_expected"] = str(marker_expected)
        updated["compiled_ex5_configured"] = True
        return updated

    if not updated["ex5_readiness_marker_present"]:
        updated["ex5_marker_issue"] = "compiled_ex5_marker_missing"
        return updated
    if marker.suffix.lower() != ".ex5":
        updated["ex5_marker_issue"] = "compiled_ex5_path_missing"
        return updated
    if _is_marker_stale(marker, marker_max_age_seconds):
        updated["ex5_readiness_marker_stale"] = True
        updated["ex5_marker_issue"] = "compiled_ex5_marker_stale"
        return updated

    updated["compiled_ex5_expected"] = str(marker)
    updated["compiled_ex5_configured"] = True
    return updated


def validate_real_mt5_runtime_contract(contract: dict[str, object]) -> list[str]:
    issues: list[str] = []
    marker_issue = str(contract.get("ex5_marker_issue", "") or "")
    if not bool(contract.get("operator_gate_approved")):
        issues.append("operator_gate_not_approved")
    if not str(contract.get("expert_path", "") or "").strip():
        issues.append("expert_path_missing")
    if not bool(contract.get("ex5_readiness_marker_present")):
        issues.append(marker_issue or "compiled_ex5_marker_missing")
    elif bool(contract.get("ex5_readiness_marker_stale")):
        issues.append("compiled_ex5_marker_stale")
    elif not bool(contract.get("compiled_ex5_configured")):
        issues.append("compiled_ex5_ready_but_not_attached_to_runtime")
    if not str(contract.get("compiled_ex5_expected", "") or "").strip():
        if bool(contract.get("ex5_readiness_marker_present")) and not bool(contract.get("ex5_readiness_marker_stale")):
            issues.append("compiled_ex5_ready_but_not_attached_to_runtime")
        else:
            issues.append(marker_issue or "compiled_ex5_path_missing")
    if int(contract.get("max_backtests", 0) or 0) != 1:
        issues.append("max_backtests_must_equal_1")
    if not bool(contract.get("smoke_only")):
        issues.append("smoke_only_required")
    if str(contract.get("close_after_run_policy", "") or "") != "always_after_real_run":
        issues.append("close_after_run_policy_missing")
    if bool(contract.get("tournament_100_run")):
        issues.append("tournament_100_run_blocked")
    if bool(contract.get("credentials_stored")):
        issues.append("credentials_must_not_be_stored")
    return list(dict.fromkeys(issues))


def build_real_mt5_runtime_contract(
    project_root: Path,
    *,
    environment: dict[str, object] | None = None,
    operator_gate_approved: bool = True,
    expert_path: str = DEFAULT_EXPERT,
    symbol: str = "XAUUSD",
    timeframe: str = "M5",
    run_id: str = "mvp_014h_runtime_dry_run",
    report_contract: dict[str, object] | None = None,
    tester_ini_text: str | None = None,
    max_backtests: int = 1,
    smoke_only: bool = True,
    close_after_run_policy: str = "always_after_real_run",
    marker_path: Path | None = None,
    marker_max_age_seconds: int = DEFAULT_MARKER_MAX_AGE_SECONDS,
) -> dict[str, object]:
    env = environment or build_local_mt5_environment_status()
    report = report_contract or build_strategy_tester_report_contract(run_id)
    tester_text = tester_ini_text or _build_tester_ini(expert_path, symbol, timeframe, report)
    contract: dict[str, object] = {
        "operator_gate_approved": operator_gate_approved,
        "ready_for_retry": False,
        "ex5_readiness_marker_present": False,
        "ex5_readiness_marker_stale": False,
        "compiled_ex5_configured": False,
        "compiled_ex5_expected": "",
        "expert_path": expert_path,
        "symbol": symbol,
        "timeframe": timeframe,
        "max_backtests": max_backtests,
        "smoke_only": smoke_only,
        "close_after_run_policy": close_after_run_policy,
        "tournament_100_run": False,
        "credentials_stored": False,
        "environment": env,
        "tester_ini_text": tester_text,
        "report_contract": report,
    }
    contract = attach_ex5_readiness_to_runtime_contract(
        project_root,
        contract,
        marker_path=marker_path,
        marker_max_age_seconds=marker_max_age_seconds,
    )
    contract_issues = validate_real_mt5_runtime_contract(contract)
    runtime_preflight = build_real_mt5_preflight_check(
        RealMT5PreflightConfig(
            terminal_found=bool(env.get("terminal_found")),
            metaeditor_found=bool(env.get("metaeditor_found")),
            expert=expert_path,
            expected_ex5_path=str(contract.get("compiled_ex5_expected", "") or ""),
            symbol=symbol,
            period=timeframe,
            max_backtests=max_backtests,
            smoke_only=smoke_only,
            operator_gate_approved=operator_gate_approved,
            close_after_run_policy=close_after_run_policy,
            tournament_100_run=False,
            credentials_stored=False,
        ),
        report,
        {"candidate_id": run_id, "expert": expert_path},
        tester_ini_text=tester_text,
    )
    terminal_contract = build_terminal_contract_audit(
        project_root,
        environment=env,
        expert=expert_path,
        symbol=symbol,
        timeframe=timeframe,
        tester_ini_text=tester_text,
        report_contract=report,
        allow_external_filesystem_check=False,
    )
    terminal_readiness = dict(terminal_contract.get("readiness", {})) or public_readiness_summary(
        validate_compiled_ex5_readiness(
            project_root,
            environment=env,
            expert_relative_path=expert_path,
            allow_external_filesystem_check=False,
        )
    )
    all_issues = list(
        dict.fromkeys(
            [
                *contract_issues,
                *list(runtime_preflight.get("blocking_issues", [])),
                *list(terminal_contract.get("blocking_issues", [])),
            ]
        )
    )
    ready = (
        not all_issues
        and bool(runtime_preflight.get("ready_for_real_retry"))
        and bool(terminal_contract.get("ready_for_real_retry"))
    )
    root_cause = (
        "compiled_ex5_ready_but_not_attached_to_runtime"
        if "compiled_ex5_ready_but_not_attached_to_runtime" in all_issues
        else "compiled_ex5_ready_but_not_attached_to_runtime"
        if ready
        else "runtime_contract_blocked"
    )
    runtime = RealMT5RuntimeContract(
        operator_gate_approved=operator_gate_approved,
        ready_for_retry=ready,
        ex5_readiness_marker_present=bool(contract.get("ex5_readiness_marker_present")),
        ex5_readiness_marker_stale=bool(contract.get("ex5_readiness_marker_stale")),
        compiled_ex5_configured=bool(contract.get("compiled_ex5_configured")),
        compiled_ex5_expected=str(contract.get("compiled_ex5_expected", "") or ""),
        expert_path=expert_path,
        symbol=symbol,
        timeframe=timeframe,
        max_backtests=max_backtests,
        smoke_only=smoke_only,
        close_after_run_policy=close_after_run_policy,
        tournament_100_run=False,
        credentials_stored=False,
        tester_ini_contract=dict(runtime_preflight.get("tester_ini_contract_summary", {})),
        report_contract=dict(runtime_preflight.get("report_contract_summary", {})),
        runtime_preflight=runtime_preflight,
        root_cause=root_cause,
        terminal_contract_audit_required=True,
        compiled_ex5_verified_in_terminal_datadir=bool(
            terminal_readiness["compiled_ex5_verified_in_terminal_datadir"]
        ),
        terminal_datadir_consistent=bool(terminal_readiness["terminal_datadir_consistent"]),
        expert_mapping_valid_for_tester=bool(terminal_readiness["expert_mapping_valid_for_strategy_tester"]),
        blocking_issues=all_issues,
        warnings=list(runtime_preflight.get("warnings", [])),
    )
    return runtime.to_dict()


def make_runtime_contract_summary(runtime_contract: dict[str, object]) -> dict[str, object]:
    runtime_preflight = runtime_contract.get("runtime_preflight", {})
    payload = {
        "status": "PASS_MVP_014H_RUNTIME_DRY_RUN_READY"
        if runtime_contract.get("ready_for_retry")
        else "HOLD_MVP_014H_RUNTIME_DRY_RUN_BLOCKED",
        "runtime_handoff_diagnosed": True,
        "root_cause": runtime_contract.get("root_cause", ""),
        "runtime_handoff_fix": "fixed" if runtime_contract.get("ready_for_retry") else "blocked",
        "runtime_contract_created": True,
        "ex5_marker_attached_to_runtime": bool(runtime_contract.get("compiled_ex5_configured")),
        "compiled_ex5_configured": bool(runtime_contract.get("compiled_ex5_configured")),
        "compiled_ex5_expected": runtime_contract.get("compiled_ex5_expected", ""),
        "ex5_readiness_marker_present": bool(runtime_contract.get("ex5_readiness_marker_present")),
        "ex5_readiness_marker_stale": bool(runtime_contract.get("ex5_readiness_marker_stale")),
        "ready_for_real_retry": bool(runtime_contract.get("ready_for_retry")),
        "terminal_contract_audit_required": bool(runtime_contract.get("terminal_contract_audit_required")),
        "compiled_ex5_verified_in_terminal_datadir": bool(
            runtime_contract.get("compiled_ex5_verified_in_terminal_datadir")
        ),
        "terminal_datadir_consistent": bool(runtime_contract.get("terminal_datadir_consistent")),
        "expert_mapping_valid_for_tester": bool(runtime_contract.get("expert_mapping_valid_for_tester")),
        "blocking_issues": runtime_contract.get("blocking_issues", []),
        "warnings": runtime_contract.get("warnings", []),
        "runtime_preflight_status": runtime_preflight.get("status", ""),
        "runtime_preflight_ready": bool(runtime_preflight.get("ready_for_real_retry", False)),
        "operator_gate_approved": bool(runtime_contract.get("operator_gate_approved")),
        "expert_path": runtime_contract.get("expert_path", ""),
        "max_backtests": runtime_contract.get("max_backtests", 0),
        "smoke_only": bool(runtime_contract.get("smoke_only")),
        "close_after_run_policy": runtime_contract.get("close_after_run_policy", ""),
        "report_contract": runtime_contract.get("report_contract", {}),
        "tester_ini_contract": runtime_contract.get("tester_ini_contract", {}),
        "mt5_real_run_new": False,
        "backtest_real_run_new": False,
        "strategy_tester_run_new": False,
        "ea_executed_new": False,
        "tournament_100_run": False,
        "exe_created": False,
        "zip_created": False,
        "credentials_stored": False,
        "private_files_committed": False,
        "paths_sanitized": True,
        "public_summary_created": True,
        "next_step": "operator may approve MVP-014L only after review and fresh Operator Gate approval"
        if bool(runtime_preflight.get("ready_for_real_retry"))
        else "retry remains blocked until terminal DataDir and expert mapping diagnostics pass",
    }
    return sanitize_runtime_contract_summary(payload)


def _runtime_dry_run_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# MVP-014H Runtime Preflight Marker Handoff",
        "",
        f"- Status: {payload['status']}",
        f"- Runtime handoff diagnosed: {str(payload['runtime_handoff_diagnosed']).lower()}",
        f"- Root cause: {payload['root_cause']}",
        f"- Runtime contract created: {str(payload['runtime_contract_created']).lower()}",
        f"- EX5 marker attached to runtime: {str(payload['ex5_marker_attached_to_runtime']).lower()}",
        f"- Compiled EX5 configured: {str(payload['compiled_ex5_configured']).lower()}",
        f"- Ready for real retry: {str(payload['ready_for_real_retry']).lower()}",
        f"- Blocking issues: {', '.join(payload['blocking_issues']) if payload['blocking_issues'] else 'none'}",
        f"- Warnings: {', '.join(payload['warnings']) if payload['warnings'] else 'none'}",
        f"- Runtime preflight status: {payload['runtime_preflight_status']}",
        f"- Runtime preflight ready: {str(payload['runtime_preflight_ready']).lower()}",
        f"- MT5 real run new: {str(payload['mt5_real_run_new']).lower()}",
        f"- Backtest real run new: {str(payload['backtest_real_run_new']).lower()}",
        f"- Strategy Tester run new: {str(payload['strategy_tester_run_new']).lower()}",
        f"- EA executed new: {str(payload['ea_executed_new']).lower()}",
        f"- Tournament 100 run: {str(payload['tournament_100_run']).lower()}",
        f"- Credentials stored: {str(payload['credentials_stored']).lower()}",
        f"- Paths sanitized: {str(payload['paths_sanitized']).lower()}",
        "",
        "This dry-run builds the same runtime contract used by the real smoke path without launching MT5.",
    ]
    return "\n".join(lines) + "\n"


def generate_real_mt5_runtime_dry_run(
    project_root: Path,
    *,
    environment_override: dict[str, object] | None = None,
) -> dict[str, object]:
    runtime_contract = build_real_mt5_runtime_contract(
        project_root,
        environment=environment_override,
        operator_gate_approved=True,
        run_id="mvp_014h_runtime_dry_run",
    )
    payload = make_runtime_contract_summary(runtime_contract)
    public_json = project_root / PUBLIC_RUNTIME_DRY_RUN_JSON
    public_md = project_root / PUBLIC_RUNTIME_DRY_RUN_MD
    public_report = project_root / PUBLIC_RUNTIME_DRY_RUN_REPORT
    public_json.parent.mkdir(parents=True, exist_ok=True)
    public_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown = _runtime_dry_run_markdown(payload)
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
