"""Risk profile ranking for tournament results.

MVP-007 ranks the same candidate set under explicit risk profiles. It records
drawdown tolerance and risk flags without blocking wild research candidates.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RISK_PROFILES = {
    "controlled_risk": {
        "label": "Controlled Risk Mode",
        "max_drawdown": 20.0,
        "allow_grid": False,
        "allow_martingale": False,
        "allow_no_stop": False,
    },
    "wild": {
        "label": "Wild Mode",
        "max_drawdown": 100.0,
        "allow_grid": True,
        "allow_martingale": True,
        "allow_no_stop": True,
    },
}


@dataclass(frozen=True)
class RiskProfileRankingResult:
    status: str
    profiles: dict[str, list[dict[str, Any]]]
    champion_by_profile: dict[str, dict[str, Any] | None]
    output_path: str


def _is_candidate_allowed(candidate: dict[str, Any], profile: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    drawdown = float(candidate.get("drawdown", 0) or 0)
    risk_flags = set(candidate.get("risk_flags", []))

    if drawdown > float(profile["max_drawdown"]):
        reasons.append("drawdown_above_profile_limit")
    if "grid_enabled" in risk_flags and not profile["allow_grid"]:
        reasons.append("grid_not_allowed_in_profile")
    if "martingale_enabled" in risk_flags and not profile["allow_martingale"]:
        reasons.append("martingale_not_allowed_in_profile")
    if "no_stop" in risk_flags and not profile["allow_no_stop"]:
        reasons.append("no_stop_not_allowed_in_profile")
    return not reasons, reasons


def rank_by_risk_profile(candidates: list[dict[str, Any]], dd_max_tolerated: float | None = None) -> dict[str, list[dict[str, Any]]]:
    """Rank candidates for each profile by profit, after profile filtering."""

    rankings: dict[str, list[dict[str, Any]]] = {}
    for profile_id, profile in RISK_PROFILES.items():
        effective_profile = dict(profile)
        if dd_max_tolerated is not None:
            effective_profile["max_drawdown"] = min(float(profile["max_drawdown"]), float(dd_max_tolerated))

        rows: list[dict[str, Any]] = []
        for candidate in candidates:
            allowed, rejection_reasons = _is_candidate_allowed(candidate, effective_profile)
            row = {
                "candidate_id": candidate["candidate_id"],
                "seed_id": candidate.get("seed_id", ""),
                "mutation_origin": candidate.get("mutation_origin", ""),
                "profit": candidate.get("profit", 0),
                "drawdown": candidate.get("drawdown", 0),
                "trades": candidate.get("trades", 0),
                "risk_flags": candidate.get("risk_flags", []),
                "risk_profile": profile_id,
                "risk_mode": "wild" if profile_id == "wild" else "controlled_risk",
                "profile_id": profile_id,
                "profile_label": effective_profile["label"],
                "max_drawdown_tolerated": effective_profile["max_drawdown"],
                "max_drawdown_tolerated_pct": effective_profile["max_drawdown"],
                "ranking_profile": "wild_profit" if profile_id == "wild" else "controlled_risk",
                "profile_allowed": allowed,
                "profile_rejection_reasons": rejection_reasons,
                "accepted_by_profile": allowed,
                "rejected_by_profile_reason": rejection_reasons,
                "ranking_metric": "profit",
            }
            if profile_id == "wild":
                row["ranking_reason"] = (
                    "Wild Mode accepted this candidate because profit ranked highest and max drawdown "
                    f"tolerance was {effective_profile['max_drawdown']}%."
                )
            elif allowed:
                row["ranking_reason"] = (
                    "Controlled Risk accepted this candidate inside "
                    f"{effective_profile['max_drawdown']}% max drawdown tolerance with no disallowed risk flags."
                )
            else:
                row["ranking_reason"] = (
                    "Controlled Risk rejected or downgraded this candidate because "
                    f"{', '.join(rejection_reasons) if rejection_reasons else 'profile constraints were not met'}."
                )
            rows.append(row)

        ranked = sorted(rows, key=lambda item: (item["profile_allowed"], float(item["profit"]), item["candidate_id"]), reverse=True)
        for index, item in enumerate(ranked, start=1):
            item["profile_rank"] = index
        rankings[profile_id] = ranked
    return rankings


def select_profile_champions(rankings: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any] | None]:
    champions: dict[str, dict[str, Any] | None] = {}
    for profile_id, rows in rankings.items():
        champions[profile_id] = next((row for row in rows if row["profile_allowed"]), None)
    return champions


def generate_risk_profile_report(
    tournament_ranking_path: Path,
    output_path: Path,
    *,
    dd_max_tolerated: float | None = None,
) -> RiskProfileRankingResult:
    ranking = json.loads(tournament_ranking_path.read_text(encoding="utf-8"))
    profile_rankings = rank_by_risk_profile(ranking, dd_max_tolerated=dd_max_tolerated)
    champions = select_profile_champions(profile_rankings)
    payload = {
        "status": "risk_profile_ranking_completed",
        "dd_max_tolerated_override": dd_max_tolerated,
        "profiles": profile_rankings,
        "champion_by_profile": champions,
        "mt5_real_run": False,
        "backtest_real_run": False,
        "loop_execution": False,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return RiskProfileRankingResult(
        status="risk_profile_ranking_completed",
        profiles=profile_rankings,
        champion_by_profile=champions,
        output_path=str(output_path),
    )
