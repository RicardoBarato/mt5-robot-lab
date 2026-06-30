"""Controlled MT5 Strategy Tester smoke runner.

The runner is intentionally single-run only. It can prepare a Strategy Tester
command, but real execution is disabled unless a caller passes an explicit
authorization flag and a complete terminal/config path.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.backtest_parser import BacktestMetrics, empty_smoke_metrics
from app.core.mt5_detection import (
    detect_mt5,
    redact_public_path,
    resolve_mt5_execution_paths,
    validate_mt5_executable_path,
    validate_tester_config_path,
)
from app.core.mt5_process_control import (
    MT5ClosePolicy,
    close_mt5_after_run,
    default_mt5_close_policy,
    find_mt5_processes,
    make_app_owned_process_info,
    make_mt5_close_summary,
)
from app.core.operator_gate import BLOCKED_REASON, is_real_mt5_execution_allowed
from app.core.strategy_tester_report_config import sanitize_report_export_summary


@dataclass(frozen=True)
class MT5SmokeConfig:
    symbol: str = "XAUUSD"
    timeframe: str = "M5"
    candidate_id: str = "xauusd_base_seed"
    initial_balance_usd: int = 10000
    max_backtests: int = 1
    timeout_seconds: int = 900


@dataclass(frozen=True)
class MT5SmokeRunResult:
    symbol: str
    timeframe: str
    profit: float
    drawdown: float
    trades: int
    winrate: float
    profit_factor: float
    status: str
    candidate_id: str
    initial_balance_usd: int
    mt5_real_execution: bool
    strategy_tester_executed: bool
    loop_execution: bool
    terminal_path: str
    command: list[str]
    reason: str
    mt5_close_policy: str = "not_applicable"
    mt5_close_attempted: bool = False
    mt5_closed_after_run: bool = False
    mt5_close_method: str = "not_applicable"
    mt5_close_error: str = ""
    mt5_process_owned_by_app: bool = False
    mt5_external_process_detected: bool = False
    manual_close_required: bool = False

    def public_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["profit"] = _clean_number(payload["profit"])
        payload["drawdown"] = _clean_number(payload["drawdown"])
        payload["winrate"] = _clean_number(payload["winrate"])
        payload["profit_factor"] = _clean_number(payload["profit_factor"])
        payload["mt5_real_run"] = payload["mt5_real_execution"]
        payload["backtest_real_run"] = payload["strategy_tester_executed"]
        return payload


class MT5SmokeExecutionError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        attempted_process: bool,
        strategy_tester_requested: bool,
        return_code: int | None = None,
        command: list[str] | None = None,
        failure_stage: str = "unknown_failure_stage",
        exit_code_category: str = "not_recorded",
        close_summary: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.attempted_process = attempted_process
        self.strategy_tester_requested = strategy_tester_requested
        self.return_code = return_code
        self.command = command or []
        self.failure_stage = failure_stage
        self.exit_code_category = exit_code_category
        self.close_summary = make_mt5_close_summary(close_summary)


def _clean_number(value: object) -> int | float:
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value  # type: ignore[return-value]


def build_strategy_tester_command(
    terminal_path: str,
    tester_config_path: str,
    *,
    allowed_roots: list[Path] | None = None,
) -> list[str]:
    terminal = validate_mt5_executable_path(terminal_path, "terminal64.exe")
    tester_config = validate_tester_config_path(tester_config_path, allowed_roots=allowed_roots)
    return [str(terminal), f"/config:{tester_config}"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _report_contract_manifest_fields(report_contract: dict[str, object] | None) -> dict[str, object]:
    if not report_contract:
        return {
            "report_export_configured": False,
            "report_base": "",
            "replace_report": False,
            "shutdown_terminal": False,
            "expected_report_paths": [],
            "report_required": False,
            "parse_required": False,
            "private_artifacts_only": True,
            "public_summary_sanitized": True,
        }
    sanitized = sanitize_report_export_summary(report_contract)
    return {
        "report_export_configured": bool(sanitized.get("report_export_configured", False)),
        "report_base": str(sanitized.get("report_base", "")),
        "replace_report": bool(sanitized.get("replace_report", False)),
        "shutdown_terminal": bool(sanitized.get("shutdown_terminal", False)),
        "expected_report_paths": list(sanitized.get("expected_report_paths", [])),
        "report_required": bool(sanitized.get("report_required", False)),
        "parse_required": bool(sanitized.get("parse_required", False)),
        "private_artifacts_only": bool(sanitized.get("private_artifacts_only", True)),
        "public_summary_sanitized": bool(sanitized.get("public_summary_sanitized", True)),
    }


def _write_private_execution_artifacts(
    private_artifact_dir: Path | None,
    *,
    command: list[str],
    completed: subprocess.CompletedProcess[str] | None = None,
    error: BaseException | None = None,
    close_summary: dict[str, object] | None = None,
    report_contract: dict[str, object] | None = None,
    preflight_summary: dict[str, object] | None = None,
    failure_stage: str = "",
    exit_code_category: str = "",
) -> None:
    if private_artifact_dir is None:
        return
    private_artifact_dir.mkdir(parents=True, exist_ok=True)
    sanitized_command = [
        redact_public_path(command[0]) if command else "",
        command[1].split(":", 1)[0] + ":" + redact_public_path(command[1].split(":", 1)[1])
        if len(command) > 1 and command[1].startswith("/config:")
        else (command[1] if len(command) > 1 else ""),
    ]
    manifest = {
        "created_at": _utc_now(),
        "command_sanitized": sanitized_command,
        "raw_stdout_private_file": "stdout.txt",
        "raw_stderr_private_file": "stderr.txt",
        "returncode": completed.returncode if completed is not None else None,
        "error_type": type(error).__name__ if error else "",
        "error_message": str(error) if error else "",
        "failure_stage": failure_stage,
        "exit_code_category": exit_code_category,
        "preflight_status": preflight_summary.get("status", "") if preflight_summary else "",
        "ready_for_real_retry": bool(preflight_summary.get("ready_for_real_retry", False)) if preflight_summary else False,
        "preflight_blocking_issues": list(preflight_summary.get("blocking_issues", [])) if preflight_summary else [],
        "credentials_stored": False,
        **_report_contract_manifest_fields(report_contract),
        **make_mt5_close_summary(close_summary),
    }
    (private_artifact_dir / "execution_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (private_artifact_dir / "stdout.txt").write_text(
        completed.stdout if completed is not None else "",
        encoding="utf-8",
        errors="ignore",
    )
    (private_artifact_dir / "stderr.txt").write_text(
        completed.stderr if completed is not None else "",
        encoding="utf-8",
        errors="ignore",
    )


def run_mt5_smoke(
    config: MT5SmokeConfig | None = None,
    *,
    allow_real_execution: bool = False,
    operator_gate: dict[str, Any] | None = None,
    terminal_path: str | None = None,
    tester_config_path: str | None = None,
    tester_config_allowed_roots: list[Path] | None = None,
    private_artifact_dir: Path | None = None,
    metrics: BacktestMetrics | None = None,
    close_policy: MT5ClosePolicy | None = None,
    report_contract: dict[str, object] | None = None,
    preflight_summary: dict[str, object] | None = None,
    terminal_contract_audit: dict[str, object] | None = None,
) -> MT5SmokeRunResult:
    smoke_config = config or MT5SmokeConfig()
    if smoke_config.max_backtests != 1:
        raise ValueError("MVP-004 smoke runner allows exactly 1 backtest")

    parsed_metrics = metrics or empty_smoke_metrics()
    detection = detect_mt5()
    raw_terminal, _raw_metaeditor = resolve_mt5_execution_paths()
    terminal = terminal_path or (str(raw_terminal) if raw_terminal else "")
    terminal_public = redact_public_path(terminal)
    command: list[str] = []

    if not allow_real_execution:
        return MT5SmokeRunResult(
            symbol=smoke_config.symbol,
            timeframe=smoke_config.timeframe,
            profit=parsed_metrics.profit,
            drawdown=parsed_metrics.drawdown,
            trades=parsed_metrics.trades,
            winrate=parsed_metrics.winrate,
            profit_factor=parsed_metrics.profit_factor,
            status="smoke_run",
            candidate_id=smoke_config.candidate_id,
            initial_balance_usd=smoke_config.initial_balance_usd,
            mt5_real_execution=False,
            strategy_tester_executed=False,
            loop_execution=False,
            terminal_path=terminal_public,
            command=command,
            reason="real_mt5_execution_not_authorized_for_validation",
        )

    if not operator_gate or not is_real_mt5_execution_allowed(operator_gate):
        return MT5SmokeRunResult(
            symbol=smoke_config.symbol,
            timeframe=smoke_config.timeframe,
            profit=parsed_metrics.profit,
            drawdown=parsed_metrics.drawdown,
            trades=parsed_metrics.trades,
            winrate=parsed_metrics.winrate,
            profit_factor=parsed_metrics.profit_factor,
            status="blocked_by_operator_gate",
            candidate_id=smoke_config.candidate_id,
            initial_balance_usd=smoke_config.initial_balance_usd,
            mt5_real_execution=False,
            strategy_tester_executed=False,
            loop_execution=False,
            terminal_path=terminal_public,
            command=command,
            reason=BLOCKED_REASON,
        )

    if not terminal:
        raise MT5SmokeExecutionError(
            "MT5 terminal64.exe path is required for real execution",
            attempted_process=False,
            strategy_tester_requested=False,
        )
    if not tester_config_path:
        raise MT5SmokeExecutionError(
            "tester_config_path is required for real Strategy Tester execution",
            attempted_process=False,
            strategy_tester_requested=False,
        )
    if terminal_contract_audit is not None and not bool(terminal_contract_audit.get("ready_for_real_retry")):
        raise MT5SmokeExecutionError(
            "terminal contract audit blocked real Strategy Tester execution",
            attempted_process=False,
            strategy_tester_requested=False,
            return_code=None,
            command=[],
            failure_stage="terminal_contract_audit_failed_before_strategy_tester",
            exit_code_category="not_recorded",
        )

    command = build_strategy_tester_command(
        terminal,
        tester_config_path,
        allowed_roots=tester_config_allowed_roots,
    )
    policy = close_policy or default_mt5_close_policy()
    close_summary = make_mt5_close_summary(None)
    pre_existing_mt5_processes = find_mt5_processes()

    def with_external_process_state(summary: dict[str, object]) -> dict[str, object]:
        clean_summary = make_mt5_close_summary(summary)
        if pre_existing_mt5_processes:
            clean_summary["mt5_external_process_detected"] = True
            clean_summary["manual_close_required"] = True
        return clean_summary

    completed: subprocess.CompletedProcess[str] | None = None
    process_info = None
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        process_info = make_app_owned_process_info(process.pid, command[0])
        try:
            stdout, stderr = process.communicate(timeout=smoke_config.timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            close_summary = with_external_process_state(make_mt5_close_summary(close_mt5_after_run(process_info, policy)))
            _write_private_execution_artifacts(
                private_artifact_dir,
                command=command,
                error=exc,
                close_summary=close_summary,
                report_contract=report_contract,
                preflight_summary=preflight_summary,
                failure_stage="strategy_tester_timeout",
                exit_code_category="not_recorded",
            )
            raise MT5SmokeExecutionError(
                f"MT5 Strategy Tester smoke timed out after {smoke_config.timeout_seconds} seconds",
                attempted_process=True,
                strategy_tester_requested=True,
                return_code=None,
                command=[redact_public_path(command[0]), f"/config:{redact_public_path(command[1].split(':', 1)[1])}"],
                failure_stage="strategy_tester_timeout",
                exit_code_category="not_recorded",
                close_summary=close_summary,
            ) from exc
        completed = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    except subprocess.TimeoutExpired as exc:
        close_summary = with_external_process_state(make_mt5_close_summary(close_mt5_after_run(process_info, policy)))
        _write_private_execution_artifacts(
            private_artifact_dir,
            command=command,
            error=exc,
            close_summary=close_summary,
            report_contract=report_contract,
            preflight_summary=preflight_summary,
            failure_stage="strategy_tester_timeout",
            exit_code_category="not_recorded",
        )
        raise MT5SmokeExecutionError(
            f"MT5 Strategy Tester smoke timed out after {smoke_config.timeout_seconds} seconds",
            attempted_process=True,
            strategy_tester_requested=True,
            return_code=None,
            command=[redact_public_path(command[0]), f"/config:{redact_public_path(command[1].split(':', 1)[1])}"],
            failure_stage="strategy_tester_timeout",
            exit_code_category="not_recorded",
            close_summary=close_summary,
        ) from exc
    except OSError as exc:
        close_summary = with_external_process_state(make_mt5_close_summary(close_mt5_after_run(process_info, policy)))
        _write_private_execution_artifacts(
            private_artifact_dir,
            command=command,
            error=exc,
            close_summary=close_summary,
            report_contract=report_contract,
            preflight_summary=preflight_summary,
            failure_stage="strategy_tester_process_start_failed",
            exit_code_category="not_recorded",
        )
        raise MT5SmokeExecutionError(
            "MT5 Strategy Tester smoke process could not be started",
            attempted_process=False,
            strategy_tester_requested=True,
            return_code=None,
            command=[redact_public_path(command[0]), f"/config:{redact_public_path(command[1].split(':', 1)[1])}"],
            failure_stage="strategy_tester_process_start_failed",
            exit_code_category="not_recorded",
            close_summary=close_summary,
        ) from exc
    finally:
        if completed is not None:
            close_summary = with_external_process_state(make_mt5_close_summary(close_mt5_after_run(process_info, policy)))
    _write_private_execution_artifacts(
        private_artifact_dir,
        command=command,
        completed=completed,
        close_summary=close_summary,
        report_contract=report_contract,
        preflight_summary=preflight_summary,
        failure_stage="strategy_tester_completed" if completed and completed.returncode == 0 else "strategy_tester_failed_before_ea",
        exit_code_category="success" if completed and completed.returncode == 0 else "unknown_terminal_exit",
    )
    if completed.returncode != 0:
        raise MT5SmokeExecutionError(
            f"MT5 Strategy Tester smoke failed with exit code {completed.returncode}",
            attempted_process=True,
            strategy_tester_requested=True,
            return_code=completed.returncode,
            command=[redact_public_path(command[0]), f"/config:{redact_public_path(command[1].split(':', 1)[1])}"],
            failure_stage="strategy_tester_failed_before_ea",
            exit_code_category="unknown_terminal_exit",
            close_summary=close_summary,
        )

    return MT5SmokeRunResult(
        symbol=smoke_config.symbol,
        timeframe=smoke_config.timeframe,
        profit=parsed_metrics.profit,
        drawdown=parsed_metrics.drawdown,
        trades=parsed_metrics.trades,
        winrate=parsed_metrics.winrate,
        profit_factor=parsed_metrics.profit_factor,
        status="smoke_run",
        candidate_id=smoke_config.candidate_id,
        initial_balance_usd=smoke_config.initial_balance_usd,
        mt5_real_execution=True,
        strategy_tester_executed=True,
        loop_execution=False,
        terminal_path=redact_public_path(terminal),
        command=[redact_public_path(command[0]), f"/config:{redact_public_path(command[1].split(':', 1)[1])}"],
        reason="single_strategy_tester_smoke_completed",
        **close_summary,
    )


def write_smoke_result(result: MT5SmokeRunResult, output_path: Path) -> dict[str, object]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = result.public_payload()
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
