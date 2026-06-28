"""Smoke tournament engine for MT5 Robot Lab.

MVP-006 connects candidate generation, the smoke runner, result collection,
ranking and champion capture. It does not run MT5 in validation mode.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.candidate_generator import DEFAULT_SEED, generate_candidates, list_candidates, save_candidates
from app.core.champion_dna import create_champion_dna, save_champion_dna
from app.core.mt5_runner import MT5SmokeConfig, MT5SmokeRunResult, run_mt5_smoke
from app.core.risk_profile_ranking import RISK_PROFILES


MIN_CANDIDATES = 5
MAX_CANDIDATES = 20


@dataclass(frozen=True)
class TournamentResult:
    status: str
    candidates_loaded: int
    execution_done: bool
    ranking_generated: bool
    champion_selected: bool
    mt5_real_run: bool
    backtest_real_run: bool
    loop_execution: bool
    reports: dict[str, str]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_candidates(candidates_root: Path, *, min_candidates: int = MIN_CANDIDATES) -> list[dict[str, Any]]:
    """Load existing candidates or generate a finite default smoke set."""

    candidates = list_candidates(candidates_root)
    if len(candidates) < min_candidates:
        generated = generate_candidates(DEFAULT_SEED)
        save_candidates(generated, candidates_root)
        candidates = list_candidates(candidates_root)
    if len(candidates) < MIN_CANDIDATES:
        raise ValueError("Tournament smoke requires at least 5 candidates")
    if len(candidates) > MAX_CANDIDATES:
        raise ValueError("Tournament smoke allows at most 20 candidates")
    return candidates


def execute_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Execute one smoke run per candidate without MT5 real execution."""

    if not (MIN_CANDIDATES <= len(candidates) <= MAX_CANDIDATES):
        raise ValueError("Tournament smoke candidate count must be between 5 and 20")

    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        if candidate_id in seen:
            raise ValueError(f"Duplicate candidate_id: {candidate_id}")
        seen.add(candidate_id)
        seed_trace = candidate.get("seed_trace", {})
        config = MT5SmokeConfig(
            symbol=seed_trace.get("symbol", "XAUUSD"),
            timeframe=seed_trace.get("timeframe", "M5"),
            candidate_id=candidate_id,
            max_backtests=1,
        )
        smoke_result = run_mt5_smoke(config, allow_real_execution=False)
        results.append(
            {
                "candidate": candidate,
                "result": smoke_result.public_payload(),
                "execution_mode": "smoke_only",
                "backtests_executed": 1,
            }
        )
    return results


def collect_results(executions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    for execution in executions:
        candidate = execution["candidate"]
        result = execution["result"]
        collected.append(
            {
                "candidate_id": candidate["candidate_id"],
                "seed_id": candidate["seed_id"],
                "mutation_origin": candidate["mutation_origin"],
                "parameters": candidate["parameters"],
                "risk_flags": candidate["risk_flags"],
                "profit": result["profit"],
                "drawdown": result["drawdown"],
                "trades": result["trades"],
                "winrate": result["winrate"],
                "profit_factor": result["profit_factor"],
                "status": result["status"],
                "mt5_real_run": result["mt5_real_execution"],
                "backtest_real_run": result["strategy_tester_executed"],
                "loop_execution": result["loop_execution"],
            }
        )
    return collected


def rank_candidates(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(results, key=lambda item: (float(item["profit"]), item["candidate_id"]), reverse=True)
    for index, item in enumerate(ranked, start=1):
        item["rank"] = index
        item["ranking_metric"] = "profit"
    return ranked


def select_champion(ranking: list[dict[str, Any]]) -> dict[str, Any] | None:
    return ranking[0] if ranking else None


def generate_report(
    output_dir: Path,
    *,
    ranking: list[dict[str, Any]],
    champion: dict[str, Any] | None,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = _utc_now()
    result_path = output_dir / "tournament_smoke_result.json"
    ranking_path = output_dir / "tournament_ranking.json"
    summary_path = output_dir / "tournament_summary.md"
    champion_path = output_dir / "tournament_champion_dna.json"
    champion_dna_v2_path = output_dir / "sample_champion_dna_v2.json"
    champion_summary_v2_path = output_dir / "sample_champion_dna_v2.md"

    champion_dna_v2 = None
    if champion:
        risk_profile = {
            "profile_id": "wild",
            "profile_rank": champion.get("rank", 1),
            "max_drawdown_tolerated": RISK_PROFILES["wild"]["max_drawdown"],
            "profile_allowed": True,
        }
        config = {
            "lab_id": "ea-xau",
            "lab_name": "XAU Robot Lab",
            "requested_symbol": "XAUUSD",
            "broker_symbol": "XAUUSD",
            "timeframe": "M5",
            "timeframe_minutes": 5,
            "initial_balance_usd": 10000.0,
            "backtest_years": 0.0,
            "test_run_id": "tournament_smoke",
            "report_path": "reports/public/tournament_summary.md",
            "status": "smoke_or_dry_run",
            "mt5_real_run": False,
            "backtest_real_run": False,
            "notes": "Generated by MVP-006/008 smoke tournament integration.",
        }
        metrics = {
            "profit": champion.get("profit", 0),
            "drawdown": champion.get("drawdown", 0),
            "trades": champion.get("trades", 0),
            "winrate": champion.get("winrate", 0),
            "profit_factor": champion.get("profit_factor", 0),
        }
        champion_dna_v2 = create_champion_dna(champion, metrics, config, risk_profile)
        save_champion_dna(champion_dna_v2, output_dir)

    result_payload = {
        "status": "tournament_smoke_completed",
        "created_at": created_at,
        "candidate_count": len(ranking),
        "ranking_metric": "profit",
        "mt5_real_run": False,
        "backtest_real_run": False,
        "loop_execution": False,
        "champion": champion,
        "champion_dna_v2": champion_dna_v2.champion_id if champion_dna_v2 else None,
    }
    result_path.write_text(json.dumps(result_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ranking_path.write_text(json.dumps(ranking, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    champion_path.write_text(json.dumps(champion or {}, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    champion_id = champion["candidate_id"] if champion else "none"
    champion_profit = champion["profit"] if champion else "n/a"
    summary = [
        "# Tournament Smoke Summary",
        "",
        "- Mode: smoke only",
        "- Ranking metric: profit",
        f"- Candidates loaded: {len(ranking)}",
        "- MT5 real run: false",
        "- Backtest real run: false",
        "- Loop execution: false",
        f"- Champion: {champion_id}",
        f"- Champion profit: {champion_profit}",
        "",
        "This MVP connects candidate generation, smoke execution, result collection, ranking and champion capture without running MT5.",
    ]
    summary_path.write_text("\n".join(summary) + "\n", encoding="utf-8")

    return {
        "result": str(result_path),
        "ranking": str(ranking_path),
        "summary": str(summary_path),
        "champion_dna": str(champion_path),
        "champion_dna_v2": str(champion_dna_v2_path),
        "champion_public_summary_v2": str(champion_summary_v2_path),
    }


def run_tournament(project_root: Path, *, candidates_root: Path | None = None) -> TournamentResult:
    candidates_path = candidates_root or project_root / "candidates"
    output_dir = project_root / "reports" / "public"
    candidates = load_candidates(candidates_path)
    executions = execute_candidates(candidates)
    collected = collect_results(executions)
    ranking = rank_candidates(collected)
    champion = select_champion(ranking)
    reports = generate_report(output_dir, ranking=ranking, champion=champion)

    mt5_real_run = any(item["mt5_real_run"] for item in ranking)
    backtest_real_run = any(item["backtest_real_run"] for item in ranking)
    loop_execution = any(item["loop_execution"] for item in ranking)

    return TournamentResult(
        status="tournament_smoke_completed",
        candidates_loaded=len(candidates),
        execution_done=True,
        ranking_generated=bool(ranking),
        champion_selected=champion is not None,
        mt5_real_run=mt5_real_run,
        backtest_real_run=backtest_real_run,
        loop_execution=loop_execution,
        reports=reports,
    )
