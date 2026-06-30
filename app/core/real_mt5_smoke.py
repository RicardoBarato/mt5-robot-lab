"""One-run real MT5 smoke orchestration.

This module is gated by the explicit operator phrase. It may launch the local
MT5 terminal once, writes raw artifacts only to ignored private folders and
emits public summaries with sanitized fields.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from app.core.mt5_detection import build_local_mt5_environment_status, redact_public_path
from app.core.mt5_process_control import make_mt5_close_summary
from app.core.mt5_report_parser import ParsedMT5Report, parse_mt5_report
from app.core.mt5_runner import MT5SmokeConfig, MT5SmokeExecutionError, MT5SmokeRunResult, run_mt5_smoke
from app.core.operator_gate import APPROVAL_PHRASE_PT, approve_operator_gate, create_operator_approval_request
from app.core.real_mt5_result_capture import ResultCaptureManifest, create_capture_context, write_capture_manifest
from app.core.real_mt5_runtime_contract import build_real_mt5_runtime_contract
from app.core.strategy_tester_report_config import (
    build_strategy_tester_report_contract,
    build_tester_ini_report_lines,
)
from app.core.terminal_contract_audit import build_terminal_contract_audit


DEFAULT_SYMBOL = "XAUUSD"
DEFAULT_TIMEFRAME = "M5"
DEFAULT_CANDIDATE_ID = "mt5_builtin_examples_macd_sample_smoke"
PRIVATE_SMOKE_DIR = Path("reports") / "private" / "real_mt5_smoke"
PUBLIC_SUMMARY_JSON = Path("reports") / "public" / "real_mt5_smoke_summary.json"
PUBLIC_SUMMARY_MD = Path("reports") / "public" / "real_mt5_smoke_summary.md"
PUBLIC_REPORT_MD = Path("reports") / "public" / "MVP_013C_ONE_RUN_REAL_MT5_SMOKE_REPORT.md"
PUBLIC_CAPTURE_SUMMARY_JSON = Path("reports") / "public" / "real_mt5_capture_smoke_summary.json"
PUBLIC_CAPTURE_SUMMARY_MD = Path("reports") / "public" / "real_mt5_capture_smoke_summary.md"
PUBLIC_CAPTURE_REPORT_MD = Path("reports") / "public" / "MVP_014B_ONE_RUN_REAL_CAPTURE_SMOKE_REPORT.md"


@dataclass(frozen=True)
class RealMT5SmokeSummary:
    result_status: str
    operator_gate_approved: bool
    mt5_detected: bool
    terminal_found: bool
    metaeditor_found: bool
    ready_for_real_smoke: bool
    real_smoke_attempted: bool
    runs_attempted: int
    real_smoke_runs: int
    mt5_real_run: bool
    backtest_real_run: bool
    strategy_tester_run: bool
    ea_executed: bool
    tournament_100_run: bool
    smoke_only: bool
    max_backtests: int
    strategy_tester_runs: int
    symbol_requested: str
    timeframe_requested: str
    sanitized_terminal_detected: bool
    credentials_stored: bool
    paths_sanitized: bool
    raw_artifacts_private: bool
    public_summary_created: bool
    failure_reason: str
    mt5_close_policy: str = "not_applicable"
    mt5_close_attempted: bool = False
    mt5_closed_after_run: bool = False
    mt5_close_method: str = "not_applicable"
    mt5_close_error: str = ""
    mt5_process_owned_by_app: bool = False
    mt5_external_process_detected: bool = False
    manual_close_required: bool = False
    preflight_status: str = "not_evaluated"
    ready_for_real_retry: bool = False
    preflight_blocking_issues: list[str] = field(default_factory=list)
    failure_stage: str = "not_attempted"
    exit_code_recorded: int | None = None
    exit_code_category: str = "not_recorded"
    expert_path_checked: bool = False
    compiled_ex5_checked: bool = False
    report_export_contract_checked: bool = False
    report_path_privacy_checked: bool = False
    tester_ini_contract_checked: bool = False
    terminal_launch_args_sanitized: list[str] = field(default_factory=list)
    tester_ini_contract_summary: dict[str, object] = field(default_factory=dict)
    report_contract_summary: dict[str, object] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, object]:
        return asdict(self)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sanitize_failure_reason(message: str, project_root: Path) -> str:
    sanitized = message.replace(str(project_root), "<PROJECT_ROOT>")
    sanitized = sanitized.replace(str(project_root).replace("\\", "/"), "<PROJECT_ROOT>")
    sanitized = re.sub(r"(?i)[a-z]:[\\/][^\s\"']+", "<WINDOWS_PATH_REDACTED>", sanitized)
    sanitized = re.sub(r"(?i)(\\\\|//)[^\\/\s]+[\\/][^\s\"']+", "<NETWORK_PATH_REDACTED>", sanitized)
    return sanitized


def _tester_date_window() -> tuple[str, str]:
    end = date.today()
    start = end - timedelta(days=30)
    return start.strftime("%Y.%m.%d"), end.strftime("%Y.%m.%d")


def _write_private_tester_config(private_dir: Path, *, symbol: str, timeframe: str) -> tuple[Path, dict[str, object]]:
    private_dir.mkdir(parents=True, exist_ok=True)
    from_date, to_date = _tester_date_window()
    report_contract = build_strategy_tester_report_contract(private_dir.name)
    config_path = private_dir / "mvp_013c_smoke.ini"
    config_text = "\n".join(
        [
            "[Tester]",
            "Expert=Examples\\MACD Sample",
            f"Symbol={symbol}",
            f"Period={timeframe}",
            "Model=0",
            "Optimization=0",
            f"FromDate={from_date}",
            f"ToDate={to_date}",
            "Deposit=10000",
            "Currency=USD",
            *build_tester_ini_report_lines(report_contract),
            "",
        ]
    )
    config_path.write_text(config_text, encoding="utf-8")
    return config_path, report_contract


def _write_public_summaries(project_root: Path, summary: RealMT5SmokeSummary) -> dict[str, Path]:
    public_json = project_root / PUBLIC_SUMMARY_JSON
    public_md = project_root / PUBLIC_SUMMARY_MD
    public_report = project_root / PUBLIC_REPORT_MD
    public_json.parent.mkdir(parents=True, exist_ok=True)
    payload = summary.to_public_dict()
    public_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# MVP-013C One-Run Real MT5 Smoke Summary",
        "",
        f"- Result status: {summary.result_status}",
        f"- Operator gate approved: {str(summary.operator_gate_approved).lower()}",
        f"- MT5 detected: {str(summary.mt5_detected).lower()}",
        f"- Terminal found: {str(summary.terminal_found).lower()}",
        f"- MetaEditor found: {str(summary.metaeditor_found).lower()}",
        f"- Ready for real smoke: {str(summary.ready_for_real_smoke).lower()}",
        f"- Real smoke attempted: {str(summary.real_smoke_attempted).lower()}",
        f"- Runs attempted: {summary.runs_attempted}",
        f"- Real smoke runs: {summary.real_smoke_runs}",
        f"- MT5 real run: {str(summary.mt5_real_run).lower()}",
        f"- Backtest real run: {str(summary.backtest_real_run).lower()}",
        f"- Strategy Tester run: {str(summary.strategy_tester_run).lower()}",
        f"- EA executed: {str(summary.ea_executed).lower()}",
        f"- Smoke only: {str(summary.smoke_only).lower()}",
        f"- Tournament 100 run: {str(summary.tournament_100_run).lower()}",
        f"- Symbol requested: {summary.symbol_requested}",
        f"- Timeframe requested: {summary.timeframe_requested}",
        f"- Credentials stored: {str(summary.credentials_stored).lower()}",
        f"- Paths sanitized: {str(summary.paths_sanitized).lower()}",
        f"- MT5 close policy: {summary.mt5_close_policy}",
        f"- MT5 close attempted: {str(summary.mt5_close_attempted).lower()}",
        f"- MT5 closed after run: {str(summary.mt5_closed_after_run).lower()}",
        f"- MT5 close method: {summary.mt5_close_method}",
        f"- Manual close required: {str(summary.manual_close_required).lower()}",
        f"- Preflight status: {summary.preflight_status}",
        f"- Ready for retry: {str(summary.ready_for_real_retry).lower()}",
        f"- Failure stage: {summary.failure_stage}",
        f"- Exit code recorded: {summary.exit_code_recorded if summary.exit_code_recorded is not None else 'not_recorded'}",
        f"- Exit code category: {summary.exit_code_category}",
        f"- Expert path checked: {str(summary.expert_path_checked).lower()}",
        f"- Compiled EX5 checked: {str(summary.compiled_ex5_checked).lower()}",
        f"- Report export contract checked: {str(summary.report_export_contract_checked).lower()}",
        f"- Report path privacy checked: {str(summary.report_path_privacy_checked).lower()}",
        "",
        "Raw local artifacts are kept only under the ignored private smoke folder.",
    ]
    if summary.failure_reason:
        lines.extend(["", f"- Failure reason: {summary.failure_reason}"])
    public_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    public_report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": public_json, "markdown": public_md, "report": public_report}


def _select_report_file(private_dir: Path, manifest: ResultCaptureManifest) -> Path | None:
    preferred = [
        "strategy_tester_report.html",
        "strategy_tester_report.htm",
        "strategy_tester_report.xml",
        "strategy_tester_report.csv",
        "strategy_tester_report.json",
    ]
    observed = set(manifest.observed_report_files)
    for name in preferred:
        if name in observed:
            return private_dir / name
    return private_dir / manifest.observed_report_files[0] if manifest.observed_report_files else None


def _metric_payload(parsed_report: ParsedMT5Report | None) -> dict[str, object]:
    if parsed_report is None:
        return {}
    return {
        "total_trades": parsed_report.total_trades,
        "net_profit": parsed_report.net_profit,
        "gross_profit": parsed_report.gross_profit,
        "gross_loss": parsed_report.gross_loss,
        "max_drawdown": parsed_report.max_drawdown,
        "initial_deposit": parsed_report.initial_deposit,
        "symbol": parsed_report.symbol,
        "timeframe": parsed_report.timeframe,
        "started_at": parsed_report.started_at,
        "ended_at": parsed_report.ended_at,
    }


def _metrics_extracted(parsed_report: ParsedMT5Report | None) -> bool:
    if parsed_report is None or not parsed_report.parseable:
        return False
    metrics = _metric_payload(parsed_report)
    return any(value is not None for value in metrics.values())


def _capture_result_status(
    summary: RealMT5SmokeSummary,
    *,
    report_file_found: bool,
    parsed_report: ParsedMT5Report | None,
) -> str:
    if summary.result_status == "HOLD_REAL_SMOKE_FAILED_NO_RETRY":
        return "HOLD_REAL_CAPTURE_SMOKE_FAILED_NO_RETRY"
    if not summary.real_smoke_attempted:
        return summary.result_status
    if not report_file_found:
        return "HOLD_REAL_CAPTURE_SMOKE_NO_REPORT_FOUND"
    if parsed_report and parsed_report.parseable:
        return "PASS_MVP_014B_REAL_CAPTURE_SMOKE_PARSEABLE"
    return "HOLD_REAL_CAPTURE_SMOKE_UNPARSEABLE"


def _write_public_capture_summaries(
    project_root: Path,
    *,
    summary: RealMT5SmokeSummary,
    manifest: ResultCaptureManifest,
    parsed_report: ParsedMT5Report | None,
    report_file_found: bool,
    parse_status: str,
) -> dict[str, object]:
    metrics_extracted = _metrics_extracted(parsed_report)
    result_status = _capture_result_status(summary, report_file_found=report_file_found, parsed_report=parsed_report)
    public_json = project_root / PUBLIC_CAPTURE_SUMMARY_JSON
    public_md = project_root / PUBLIC_CAPTURE_SUMMARY_MD
    public_report = project_root / PUBLIC_CAPTURE_REPORT_MD
    public_json.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "result_status": result_status,
        "mt5_real_run": summary.mt5_real_run,
        "backtest_real_run": summary.backtest_real_run,
        "strategy_tester_run": summary.strategy_tester_run,
        "ea_executed": summary.ea_executed,
        "smoke_only": True,
        "runs_attempted": summary.runs_attempted,
        "real_smoke_runs": summary.real_smoke_runs,
        "tournament_100_run": False,
        "capture_enabled": True,
        "parse_enabled": True,
        "capture_status": manifest.capture_status,
        "parse_status": parse_status,
        "parseable": bool(parsed_report.parseable) if parsed_report else False,
        "metrics_extracted": metrics_extracted,
        "report_file_found": report_file_found,
        "observed_report_files": manifest.observed_report_files,
        "observed_log_files": manifest.observed_log_files,
        "return_code": manifest.return_code,
        "symbol_requested": summary.symbol_requested,
        "timeframe_requested": summary.timeframe_requested,
        "credentials_stored": False,
        "paths_sanitized": True,
        "raw_artifacts_private": True,
        "report_export_configured": manifest.report_export_configured,
        "report_base": manifest.report_base,
        "replace_report": manifest.replace_report,
        "shutdown_terminal": manifest.shutdown_terminal,
        "report_capture_attempted": manifest.report_capture_attempted,
        "report_capture_status": manifest.report_capture_status,
        "parser_attempted": manifest.parser_attempted,
        "failure_reason": summary.failure_reason,
        "mt5_close_policy": summary.mt5_close_policy,
        "mt5_close_attempted": summary.mt5_close_attempted,
        "mt5_closed_after_run": summary.mt5_closed_after_run,
        "mt5_close_method": summary.mt5_close_method,
        "mt5_close_error": summary.mt5_close_error,
        "mt5_process_owned_by_app": summary.mt5_process_owned_by_app,
        "mt5_external_process_detected": summary.mt5_external_process_detected,
        "manual_close_required": summary.manual_close_required,
        "preflight_status": summary.preflight_status,
        "ready_for_real_retry": summary.ready_for_real_retry,
        "preflight_blocking_issues": summary.preflight_blocking_issues,
        "failure_stage": summary.failure_stage,
        "exit_code_recorded": summary.exit_code_recorded,
        "exit_code_category": summary.exit_code_category,
        "expert_path_checked": summary.expert_path_checked,
        "compiled_ex5_checked": summary.compiled_ex5_checked,
        "report_export_contract_checked": summary.report_export_contract_checked,
        "report_path_privacy_checked": summary.report_path_privacy_checked,
        "tester_ini_contract_checked": summary.tester_ini_contract_checked,
        "terminal_launch_args_sanitized": summary.terminal_launch_args_sanitized,
        "tester_ini_contract_summary": summary.tester_ini_contract_summary,
        "report_contract_summary": summary.report_contract_summary,
        "parser_warnings": parsed_report.warnings if parsed_report else [],
        "metrics": _metric_payload(parsed_report),
    }
    public_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# MVP-014B One-Run Real Capture Smoke Summary",
        "",
        f"- Result status: {result_status}",
        f"- MT5 real run: {str(summary.mt5_real_run).lower()}",
        f"- Backtest real run: {str(summary.backtest_real_run).lower()}",
        f"- Strategy Tester run: {str(summary.strategy_tester_run).lower()}",
        f"- EA executed: {str(summary.ea_executed).lower()}",
        f"- Runs attempted: {summary.runs_attempted}",
        f"- Real smoke runs: {summary.real_smoke_runs}",
        "- Tournament 100 run: false",
        "- Capture enabled: true",
        "- Parse enabled: true",
        f"- Capture status: {manifest.capture_status}",
        f"- Report export configured: {str(manifest.report_export_configured).lower()}",
        f"- Replace report: {str(manifest.replace_report).lower()}",
        f"- Shutdown terminal: {str(manifest.shutdown_terminal).lower()}",
        f"- Parse status: {parse_status}",
        f"- Report file found: {str(report_file_found).lower()}",
        f"- Result parseable: {str(bool(parsed_report.parseable) if parsed_report else False).lower()}",
        f"- Metrics extracted: {str(metrics_extracted).lower()}",
        f"- Symbol requested: {summary.symbol_requested}",
        f"- Timeframe requested: {summary.timeframe_requested}",
        "- Credentials stored: false",
        "- Paths sanitized: true",
        f"- MT5 close policy: {summary.mt5_close_policy}",
        f"- MT5 close attempted: {str(summary.mt5_close_attempted).lower()}",
        f"- MT5 closed after run: {str(summary.mt5_closed_after_run).lower()}",
        f"- MT5 close method: {summary.mt5_close_method}",
        f"- Manual close required: {str(summary.manual_close_required).lower()}",
        f"- Preflight status: {summary.preflight_status}",
        f"- Ready for retry: {str(summary.ready_for_real_retry).lower()}",
        f"- Failure stage: {summary.failure_stage}",
        f"- Exit code recorded: {summary.exit_code_recorded if summary.exit_code_recorded is not None else 'not_recorded'}",
        f"- Exit code category: {summary.exit_code_category}",
        "",
        "Raw local artifacts remain only in the ignored private smoke folder.",
    ]
    if summary.failure_reason:
        lines.extend(["", f"- Failure reason: {summary.failure_reason}"])
    public_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    public_report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def execute_one_run_real_mt5_smoke(
    project_root: Path,
    *,
    approval_phrase: str,
    symbol: str = DEFAULT_SYMBOL,
    timeframe: str = DEFAULT_TIMEFRAME,
    run_id: str | None = None,
    runner: Callable[..., MT5SmokeRunResult] = run_mt5_smoke,
    environment_override: dict[str, object] | None = None,
    preflight_override: dict[str, object] | None = None,
) -> dict[str, object]:
    capture_context = create_capture_context(
        project_root,
        run_id=run_id,
        requested_symbol=symbol,
        requested_timeframe=timeframe,
    )
    private_dir = capture_context.run_dir
    environment = environment_override or build_local_mt5_environment_status()
    private_environment_path = private_dir / "environment_sanitized.json"
    private_environment_path.write_text(json.dumps(environment, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    gate_request = create_operator_approval_request(
        {
            "request_id": "mvp_013c_one_run_real_mt5_smoke",
            "symbol": symbol,
            "timeframe": timeframe,
            "real_execution_requested": True,
            "smoke_only": True,
            "max_backtests": 1,
            "tournament_100_run": False,
            "credentials_stored": False,
        },
        {
            "mt5_installed": environment["mt5_detected"],
            "terminal_found": environment["terminal_found"],
            "metaeditor_found": environment["metaeditor_found"],
        },
    )
    gate = approve_operator_gate(gate_request, approval_phrase)
    (private_dir / "operator_gate_manifest.json").write_text(
        json.dumps(gate, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    config_path, report_contract = _write_private_tester_config(private_dir, symbol=symbol, timeframe=timeframe)
    tester_ini_text = config_path.read_text(encoding="utf-8")
    runtime_contract = build_real_mt5_runtime_contract(
        project_root,
        environment=environment,
        operator_gate_approved=bool(gate["execution_allowed"]),
        expert_path="Examples\\MACD Sample",
        symbol=symbol,
        timeframe=timeframe,
        run_id=private_dir.name,
        report_contract=report_contract,
        tester_ini_text=tester_ini_text,
        max_backtests=1,
        smoke_only=True,
        close_after_run_policy="always_after_real_run",
    )
    terminal_contract_audit = build_terminal_contract_audit(
        project_root,
        environment=environment,
        expert="Examples\\MACD Sample",
        symbol=symbol,
        timeframe=timeframe,
        tester_ini_text=tester_ini_text,
        report_contract=report_contract,
        allow_external_filesystem_check=False,
    )
    preflight_summary = preflight_override or dict(runtime_contract["runtime_preflight"])
    if not preflight_override and runtime_contract["blocking_issues"]:
        preflight_summary = {
            **preflight_summary,
            "status": "blocked_preflight_failed",
            "ready_for_real_retry": False,
            "blocking_issues": list(runtime_contract["blocking_issues"]),
            "root_cause": runtime_contract["root_cause"],
        }
    if not preflight_override and not bool(terminal_contract_audit.get("ready_for_real_retry")):
        preflight_summary = {
            **preflight_summary,
            "status": "blocked_preflight_failed",
            "ready_for_real_retry": False,
            "blocking_issues": list(
                dict.fromkeys(
                    [
                        *list(preflight_summary.get("blocking_issues", [])),
                        *list(terminal_contract_audit.get("blocking_issues", [])),
                    ]
                )
            ),
            "root_cause": "terminal_contract_audit_failed",
            "terminal_contract_audit": terminal_contract_audit.get("terminal_contract_audit", "FAIL"),
        }
    ready_for_real_smoke = bool(
        environment["ready_for_real_smoke"]
        and gate["execution_allowed"]
        and preflight_summary.get("ready_for_real_retry", False)
    )
    status = "PASS_REAL_MT5_SMOKE_ONE_RUN_COMPLETED"
    failure_reason = ""
    attempted = False
    mt5_real_run = False
    strategy_tester_run = False
    backtest_real_run = False
    ea_executed = False
    exit_code_recorded: int | None = None
    exit_code_category = str(preflight_summary.get("exit_code_category", "not_recorded"))
    failure_stage = str(preflight_summary.get("failure_stage", "not_attempted"))
    terminal_launch_args_sanitized = list(preflight_summary.get("terminal_launch_args_sanitized", []))
    close_summary = make_mt5_close_summary(None)

    if not bool(environment["ready_for_real_smoke"] and gate["execution_allowed"]):
        status = "HOLD_MT5_NOT_READY"
    elif not bool(preflight_summary.get("ready_for_real_retry", False)):
        status = "HOLD_REAL_MT5_PREFLIGHT_BLOCKED_NO_RETRY"
        failure_reason = "real_mt5_preflight_blocked_retry"
        failure_stage = str(preflight_summary.get("failure_stage", "not_attempted"))
    else:
        attempted = True
        try:
            result = runner(
                MT5SmokeConfig(
                    symbol=symbol,
                    timeframe=timeframe,
                    candidate_id=DEFAULT_CANDIDATE_ID,
                    max_backtests=1,
                    timeout_seconds=180,
                ),
                allow_real_execution=True,
                operator_gate=gate,
                tester_config_path=str(config_path),
                tester_config_allowed_roots=[private_dir],
                private_artifact_dir=private_dir,
                report_contract=report_contract,
                preflight_summary=preflight_summary,
                terminal_contract_audit=None if preflight_override else terminal_contract_audit,
            )
            mt5_real_run = bool(result.mt5_real_execution)
            strategy_tester_run = bool(result.strategy_tester_executed)
            backtest_real_run = bool(result.strategy_tester_executed)
            ea_executed = bool(result.strategy_tester_executed)
            failure_stage = "completed_report_pending_capture"
            exit_code_recorded = 0
            exit_code_category = "success"
            terminal_launch_args_sanitized = list(result.command)
            close_summary = make_mt5_close_summary(result.public_payload())
        except MT5SmokeExecutionError as exc:
            status = "HOLD_REAL_SMOKE_FAILED_NO_RETRY"
            failure_reason = _sanitize_failure_reason(str(exc), project_root)
            mt5_real_run = bool(exc.attempted_process)
            strategy_tester_run = bool(exc.strategy_tester_requested)
            backtest_real_run = False
            ea_executed = False
            exit_code_recorded = exc.return_code
            exit_code_category = exc.exit_code_category
            failure_stage = exc.failure_stage
            terminal_launch_args_sanitized = list(exc.command)
            close_summary = make_mt5_close_summary(exc.close_summary)
        except Exception as exc:  # noqa: BLE001 - failure must be recorded without retry.
            status = "HOLD_REAL_SMOKE_FAILED_NO_RETRY"
            failure_reason = _sanitize_failure_reason(type(exc).__name__ + ": " + str(exc), project_root)
            mt5_real_run = False
            strategy_tester_run = False
            backtest_real_run = False
            ea_executed = False
            failure_stage = "runner_exception_before_strategy_tester"
            exit_code_category = "not_recorded"

    manifest = write_capture_manifest(
        capture_context,
        return_code=0 if status == "PASS_REAL_MT5_SMOKE_ONE_RUN_COMPLETED" else None,
        capture_status="process_completed" if attempted else "not_attempted",
        parse_status="pending_report_discovery",
        requested_symbol=symbol,
        requested_timeframe=timeframe,
        close_summary=close_summary,
        report_contract=report_contract,
        preflight_summary=preflight_summary,
    )

    summary = RealMT5SmokeSummary(
        result_status=status,
        operator_gate_approved=bool(gate["execution_allowed"]),
        mt5_detected=bool(environment["mt5_detected"]),
        terminal_found=bool(environment["terminal_found"]),
        metaeditor_found=bool(environment["metaeditor_found"]),
        ready_for_real_smoke=ready_for_real_smoke,
        real_smoke_attempted=attempted,
        runs_attempted=1 if attempted else 0,
        real_smoke_runs=1 if attempted else 0,
        mt5_real_run=mt5_real_run,
        backtest_real_run=backtest_real_run,
        strategy_tester_run=strategy_tester_run,
        ea_executed=ea_executed,
        tournament_100_run=False,
        smoke_only=True,
        max_backtests=1,
        strategy_tester_runs=1 if attempted else 0,
        symbol_requested=symbol,
        timeframe_requested=timeframe,
        sanitized_terminal_detected=bool(environment["terminal_path_sanitized"]),
        credentials_stored=False,
        paths_sanitized=True,
        raw_artifacts_private=True,
        public_summary_created=True,
        failure_reason=failure_reason,
        preflight_status=str(preflight_summary.get("status", "not_evaluated")),
        ready_for_real_retry=bool(preflight_summary.get("ready_for_real_retry", False)),
        preflight_blocking_issues=list(preflight_summary.get("blocking_issues", [])),
        failure_stage=failure_stage,
        exit_code_recorded=exit_code_recorded,
        exit_code_category=exit_code_category,
        expert_path_checked=bool(preflight_summary.get("expert_path_checked", False)),
        compiled_ex5_checked=bool(preflight_summary.get("compiled_ex5_checked", False)),
        report_export_contract_checked=bool(preflight_summary.get("report_export_contract_checked", False)),
        report_path_privacy_checked=bool(preflight_summary.get("report_path_privacy_checked", False)),
        tester_ini_contract_checked=bool(preflight_summary.get("tester_ini_contract_checked", False)),
        terminal_launch_args_sanitized=terminal_launch_args_sanitized,
        tester_ini_contract_summary=dict(preflight_summary.get("tester_ini_contract_summary", {})),
        report_contract_summary=dict(preflight_summary.get("report_contract_summary", {})),
        **close_summary,
    )
    public_files = _write_public_summaries(project_root, summary)
    report_file = _select_report_file(private_dir, manifest)
    parsed_report = parse_mt5_report(report_file, allowed_root=private_dir) if report_file else None
    if report_file is None:
        parse_status = "no_report_found"
        capture_status = "no_report_found" if attempted else "not_attempted"
    elif parsed_report and parsed_report.parseable:
        parse_status = "parse_success"
        capture_status = "report_found"
    else:
        parse_status = parsed_report.result_status if parsed_report else "unsupported_format_or_missing_fields"
        capture_status = "report_found"
    manifest = write_capture_manifest(
        capture_context,
        return_code=0 if status == "PASS_REAL_MT5_SMOKE_ONE_RUN_COMPLETED" else None,
        capture_status=capture_status,
        parse_status=parse_status,
        requested_symbol=symbol,
        requested_timeframe=timeframe,
        close_summary=close_summary,
        report_contract=report_contract,
        preflight_summary={
            **preflight_summary,
            "failure_stage": summary.failure_stage,
            "exit_code_category": summary.exit_code_category,
            "ready_for_real_retry": summary.ready_for_real_retry,
        },
    )
    capture_summary = _write_public_capture_summaries(
        project_root,
        summary=summary,
        manifest=manifest,
        parsed_report=parsed_report,
        report_file_found=report_file is not None,
        parse_status=parse_status,
    )
    (private_dir / "run_summary_sanitized.json").write_text(
        json.dumps(summary.to_public_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (private_dir / "run_completed_at.txt").write_text(_utc_now() + "\n", encoding="utf-8")
    return {
        "status": status,
        "summary": summary.to_public_dict(),
        "capture_summary": capture_summary,
        "public_files": {key: str(value) for key, value in public_files.items()},
        "private_artifact_dir_sanitized": redact_public_path(private_dir),
        "preflight_summary": preflight_summary,
    }


def execute_approved_one_run_smoke(project_root: Path) -> dict[str, object]:
    return execute_one_run_real_mt5_smoke(project_root, approval_phrase=APPROVAL_PHRASE_PT)
