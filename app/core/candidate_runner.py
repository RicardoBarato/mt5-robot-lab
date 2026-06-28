"""Candidate-level runner for one controlled smoke backtest."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.mt5_runner import MT5SmokeConfig, run_mt5_smoke, write_smoke_result


DEFAULT_SMOKE_RESULT = "backtest_smoke_result.json"


def run_xauusd_base_seed_smoke(
    output_dir: Path,
    *,
    allow_real_execution: bool = False,
    operator_gate: dict[str, Any] | None = None,
) -> dict[str, object]:
    """Run the single XAUUSD base-seed smoke path and write the public result."""

    config = MT5SmokeConfig()
    result = run_mt5_smoke(config, allow_real_execution=allow_real_execution, operator_gate=operator_gate)
    return write_smoke_result(result, output_dir / DEFAULT_SMOKE_RESULT)
