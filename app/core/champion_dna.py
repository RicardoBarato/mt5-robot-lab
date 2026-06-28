"""Champion DNA schema and artifact helpers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ChampionDNA:
    candidate_id: str
    rank: int
    lab_id: str
    source_mq5: str
    seed_family: str
    symbol: str
    broker_symbol: str
    timeframe: str
    years_tested: float
    initial_balance_usd: float
    net_profit_usd: float
    final_balance_usd: float
    max_drawdown_usd: float
    max_drawdown_pct: float
    profit_factor: float
    expected_payoff: float
    total_trades: int
    win_rate: float
    largest_loss_streak: int
    martingale_used: bool
    grid_used: bool
    no_stop_used: bool
    intelligence_mode: str
    codex_used: bool
    codex_authorized: bool
    mutation_mode: str
    parameter_changes: dict[str, dict[str, Any]] = field(default_factory=dict)
    code_changes_summary: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    test_run_id: str = ""
    report_path: str = ""
    notes: str = ""


def sample_champion_dna() -> ChampionDNA:
    return ChampionDNA(
        candidate_id="sample_xau_candidate_001",
        rank=1,
        lab_id="ea-xau",
        source_mq5="champions/top10/sample_xau_candidate_001.mq5",
        seed_family="xauusd_base",
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        timeframe="M5",
        years_tested=2.0,
        initial_balance_usd=10000.0,
        net_profit_usd=1250.0,
        final_balance_usd=11250.0,
        max_drawdown_usd=700.0,
        max_drawdown_pct=7.0,
        profit_factor=1.35,
        expected_payoff=12.5,
        total_trades=100,
        win_rate=42.0,
        largest_loss_streak=6,
        martingale_used=False,
        grid_used=False,
        no_stop_used=False,
        intelligence_mode="local_auto",
        codex_used=False,
        codex_authorized=False,
        mutation_mode="programmatic_local_mutation",
        parameter_changes={
            "ATR_period": {"before": 14, "after": 21},
            "ADX_min": {"before": 25, "after": 18},
            "TP_R": {"before": 2.0, "after": 3.5},
            "use_session_filter": {"before": True, "after": False},
            "martingale_enabled": {"before": False, "after": True},
        },
        code_changes_summary="Sample schema only; not performance evidence.",
        test_run_id="sample_run",
        report_path="reports/public/mt5_robot_lab_sample_summary.md",
        notes="Bootstrap sample.",
    )


def parameter_diff_markdown(dna: ChampionDNA) -> str:
    lines = ["# Parameter Diff", ""]
    for name, change in dna.parameter_changes.items():
        lines.append(f"- {name}: {change.get('before')} -> {change.get('after')}")
    return "\n".join(lines) + "\n"


def write_champion_artifacts(dna: ChampionDNA, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    dna_path = output_dir / "champion_dna.json"
    metrics_path = output_dir / "metrics.json"
    diff_path = output_dir / "parameter_diff.md"
    payload = asdict(dna)
    dna_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    metrics = {
        key: payload[key]
        for key in [
            "initial_balance_usd",
            "net_profit_usd",
            "final_balance_usd",
            "max_drawdown_usd",
            "max_drawdown_pct",
            "profit_factor",
            "expected_payoff",
            "total_trades",
            "win_rate",
        ]
    }
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    diff_path.write_text(parameter_diff_markdown(dna), encoding="utf-8")
    return {"champion_dna": dna_path, "metrics": metrics_path, "parameter_diff": diff_path}
