"""Controlled MT5 Strategy Tester smoke runner.

The runner is intentionally single-run only. It can prepare a Strategy Tester
command, but real execution is disabled unless a caller passes an explicit
authorization flag and a complete terminal/config path.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.core.backtest_parser import BacktestMetrics, empty_smoke_metrics
from app.core.mt5_detection import (
    detect_mt5,
    redact_public_path,
    validate_mt5_executable_path,
    validate_tester_config_path,
)
from app.core.operator_gate import BLOCKED_REASON, is_real_mt5_execution_allowed


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

    def public_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["profit"] = _clean_number(payload["profit"])
        payload["drawdown"] = _clean_number(payload["drawdown"])
        payload["winrate"] = _clean_number(payload["winrate"])
        payload["profit_factor"] = _clean_number(payload["profit_factor"])
        payload["mt5_real_run"] = payload["mt5_real_execution"]
        payload["backtest_real_run"] = payload["strategy_tester_executed"]
        return payload


def _clean_number(value: object) -> int | float:
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value  # type: ignore[return-value]


def build_strategy_tester_command(terminal_path: str, tester_config_path: str) -> list[str]:
    terminal = validate_mt5_executable_path(terminal_path, "terminal64.exe")
    tester_config = validate_tester_config_path(tester_config_path)
    return [str(terminal), f"/config:{tester_config}"]


def run_mt5_smoke(
    config: MT5SmokeConfig | None = None,
    *,
    allow_real_execution: bool = False,
    operator_gate: dict[str, Any] | None = None,
    terminal_path: str | None = None,
    tester_config_path: str | None = None,
    metrics: BacktestMetrics | None = None,
) -> MT5SmokeRunResult:
    smoke_config = config or MT5SmokeConfig()
    if smoke_config.max_backtests != 1:
        raise ValueError("MVP-004 smoke runner allows exactly 1 backtest")

    parsed_metrics = metrics or empty_smoke_metrics()
    detection = detect_mt5()
    terminal = terminal_path or detection.terminal_path
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
        raise RuntimeError("MT5 terminal64.exe path is required for real execution")
    if not tester_config_path:
        raise ValueError("tester_config_path is required for real Strategy Tester execution")

    command = build_strategy_tester_command(terminal, tester_config_path)
    completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=smoke_config.timeout_seconds)
    if completed.returncode != 0:
        raise RuntimeError(f"MT5 Strategy Tester smoke failed with exit code {completed.returncode}")

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
    )


def write_smoke_result(result: MT5SmokeRunResult, output_path: Path) -> dict[str, object]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = result.public_payload()
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
