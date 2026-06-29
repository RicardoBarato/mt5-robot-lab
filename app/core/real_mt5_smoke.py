"""One-run real MT5 smoke orchestration.

This module is gated by the explicit operator phrase. It may launch the local
MT5 terminal once, writes raw artifacts only to ignored private folders and
emits public summaries with sanitized fields.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from app.core.mt5_detection import build_local_mt5_environment_status, redact_public_path
from app.core.mt5_runner import MT5SmokeConfig, MT5SmokeExecutionError, MT5SmokeRunResult, run_mt5_smoke
from app.core.operator_gate import APPROVAL_PHRASE_PT, approve_operator_gate, create_operator_approval_request
from app.core.real_mt5_result_capture import create_capture_context, write_capture_manifest


DEFAULT_SYMBOL = "XAUUSD"
DEFAULT_TIMEFRAME = "M5"
DEFAULT_CANDIDATE_ID = "mt5_builtin_examples_macd_sample_smoke"
PRIVATE_SMOKE_DIR = Path("reports") / "private" / "real_mt5_smoke"
PUBLIC_SUMMARY_JSON = Path("reports") / "public" / "real_mt5_smoke_summary.json"
PUBLIC_SUMMARY_MD = Path("reports") / "public" / "real_mt5_smoke_summary.md"
PUBLIC_REPORT_MD = Path("reports") / "public" / "MVP_013C_ONE_RUN_REAL_MT5_SMOKE_REPORT.md"


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


def _write_private_tester_config(private_dir: Path, *, symbol: str, timeframe: str) -> Path:
    private_dir.mkdir(parents=True, exist_ok=True)
    from_date, to_date = _tester_date_window()
    report_target = private_dir / "strategy_tester_report"
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
            f"Report={report_target}",
            "ReplaceReport=1",
            "ShutdownTerminal=1",
            "",
        ]
    )
    config_path.write_text(config_text, encoding="utf-8")
    return config_path


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
        "",
        "Raw local artifacts are kept only under the ignored private smoke folder.",
    ]
    if summary.failure_reason:
        lines.extend(["", f"- Failure reason: {summary.failure_reason}"])
    public_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    public_report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": public_json, "markdown": public_md, "report": public_report}


def execute_one_run_real_mt5_smoke(
    project_root: Path,
    *,
    approval_phrase: str,
    symbol: str = DEFAULT_SYMBOL,
    timeframe: str = DEFAULT_TIMEFRAME,
    run_id: str | None = None,
    runner: Callable[..., MT5SmokeRunResult] = run_mt5_smoke,
    environment_override: dict[str, object] | None = None,
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

    ready_for_real_smoke = bool(environment["ready_for_real_smoke"] and gate["execution_allowed"])
    config_path = _write_private_tester_config(private_dir, symbol=symbol, timeframe=timeframe)
    status = "PASS_REAL_MT5_SMOKE_ONE_RUN_COMPLETED"
    failure_reason = ""
    attempted = False
    mt5_real_run = False
    strategy_tester_run = False
    backtest_real_run = False
    ea_executed = False

    if not ready_for_real_smoke:
        status = "HOLD_MT5_NOT_READY"
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
            )
            mt5_real_run = bool(result.mt5_real_execution)
            strategy_tester_run = bool(result.strategy_tester_executed)
            backtest_real_run = bool(result.strategy_tester_executed)
            ea_executed = bool(result.strategy_tester_executed)
        except MT5SmokeExecutionError as exc:
            status = "HOLD_REAL_SMOKE_FAILED_NO_RETRY"
            failure_reason = _sanitize_failure_reason(str(exc), project_root)
            mt5_real_run = bool(exc.attempted_process)
            strategy_tester_run = bool(exc.strategy_tester_requested)
            backtest_real_run = False
            ea_executed = False
        except Exception as exc:  # noqa: BLE001 - failure must be recorded without retry.
            status = "HOLD_REAL_SMOKE_FAILED_NO_RETRY"
            failure_reason = _sanitize_failure_reason(type(exc).__name__ + ": " + str(exc), project_root)
            mt5_real_run = False
            strategy_tester_run = False
            backtest_real_run = False
            ea_executed = False

    write_capture_manifest(
        capture_context,
        return_code=0 if status == "PASS_REAL_MT5_SMOKE_ONE_RUN_COMPLETED" else None,
        capture_status="process_completed" if attempted else "not_attempted",
        parse_status="pending_report_discovery",
        requested_symbol=symbol,
        requested_timeframe=timeframe,
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
    )
    public_files = _write_public_summaries(project_root, summary)
    (private_dir / "run_summary_sanitized.json").write_text(
        json.dumps(summary.to_public_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (private_dir / "run_completed_at.txt").write_text(_utc_now() + "\n", encoding="utf-8")
    return {
        "status": status,
        "summary": summary.to_public_dict(),
        "public_files": {key: str(value) for key, value in public_files.items()},
        "private_artifact_dir_sanitized": redact_public_path(private_dir),
    }


def execute_approved_one_run_smoke(project_root: Path) -> dict[str, object]:
    return execute_one_run_real_mt5_smoke(project_root, approval_phrase=APPROVAL_PHRASE_PT)
