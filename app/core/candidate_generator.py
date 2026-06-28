"""Generate bounded MT5 robot candidates without running MT5 or backtests."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_PARAMETERS = [
    "ATR_period",
    "ADX_min",
    "TP_R",
    "SL",
    "risk_percent",
    "use_session_filter",
    "use_grid",
    "use_martingale",
    "lot_multiplier",
    "break_even",
    "trailing_stop",
]

PARAMETER_LIMITS: dict[str, tuple[float, float] | tuple[bool, bool]] = {
    "ATR_period": (5, 100),
    "ADX_min": (5, 60),
    "TP_R": (0.25, 10.0),
    "SL": (0.0, 5000.0),
    "risk_percent": (0.01, 25.0),
    "use_session_filter": (False, True),
    "use_grid": (False, True),
    "use_martingale": (False, True),
    "lot_multiplier": (1.0, 5.0),
    "break_even": (False, True),
    "trailing_stop": (False, True),
}

DEFAULT_SEED = {
    "seed_id": "xauusd_base_seed",
    "strategy_family": "xau_trend_breakout",
    "symbol": "XAUUSD",
    "timeframe": "M5",
    "parameters": {
        "ATR_period": 14,
        "ADX_min": 25,
        "TP_R": 2.0,
        "SL": 350.0,
        "risk_percent": 1.0,
        "use_session_filter": True,
        "use_grid": False,
        "use_martingale": False,
        "lot_multiplier": 1.0,
        "break_even": True,
        "trailing_stop": False,
    },
}

MUTATION_RECIPES = [
    {
        "mutation_origin": "trend_strength_variant",
        "changes": {"ADX_min": 30, "ATR_period": 21, "TP_R": 2.5},
    },
    {
        "mutation_origin": "wide_stop_asymmetric_payoff",
        "changes": {"SL": 500.0, "TP_R": 3.0, "trailing_stop": True},
    },
    {
        "mutation_origin": "sessionless_exploration",
        "changes": {"use_session_filter": False, "risk_percent": 0.75},
    },
    {
        "mutation_origin": "aggressive_grid_research",
        "changes": {"use_grid": True, "lot_multiplier": 1.35, "risk_percent": 0.5},
    },
    {
        "mutation_origin": "martingale_research_flagged",
        "changes": {"use_martingale": True, "lot_multiplier": 1.5, "risk_percent": 0.25},
    },
]


@dataclass(frozen=True)
class CandidateGenerationResult:
    candidates: list[dict[str, Any]]
    files: list[str]
    log_path: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _candidate_id(seed_id: str, mutation_origin: str, parameters: dict[str, Any]) -> str:
    payload = json.dumps({"seed_id": seed_id, "mutation_origin": mutation_origin, "parameters": parameters}, sort_keys=True)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
    return f"{seed_id}_{digest}"


def _clamp_number(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _normalize_parameter(name: str, value: Any) -> Any:
    if name not in PARAMETER_LIMITS:
        raise ValueError(f"Unsupported parameter: {name}")
    lower, upper = PARAMETER_LIMITS[name]
    if isinstance(lower, bool) and isinstance(upper, bool):
        return bool(value)
    number = _clamp_number(float(value), float(lower), float(upper))
    if name in {"ATR_period", "ADX_min"}:
        return int(round(number))
    return round(number, 4)


def _validate_seed(seed: dict[str, Any]) -> dict[str, Any]:
    if "seed_id" not in seed:
        raise ValueError("seed must include seed_id")
    if "parameters" not in seed or not isinstance(seed["parameters"], dict):
        raise ValueError("seed must include parameters")
    normalized = deepcopy(seed)
    normalized["parameters"] = {
        name: _normalize_parameter(name, seed["parameters"].get(name, DEFAULT_SEED["parameters"][name]))
        for name in ALLOWED_PARAMETERS
    }
    return normalized


def mutate_parameters(seed: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a bounded list of parameter mutations for a seed."""

    normalized_seed = _validate_seed(seed)
    base = normalized_seed["parameters"]
    mutations: list[dict[str, Any]] = []
    for recipe in MUTATION_RECIPES:
        mutated = deepcopy(base)
        for name, value in recipe["changes"].items():
            mutated[name] = _normalize_parameter(name, value)
        mutations.append(
            {
                "mutation_origin": recipe["mutation_origin"],
                "parameters": mutated,
                "changed_parameters": sorted(recipe["changes"].keys()),
            }
        )
    return mutations


def apply_constraints(candidate: dict[str, Any]) -> dict[str, Any]:
    """Normalize candidate parameters and record risk flags instead of blocking risk."""

    constrained = deepcopy(candidate)
    parameters = constrained.get("parameters", {})
    constrained["parameters"] = {name: _normalize_parameter(name, parameters.get(name)) for name in ALLOWED_PARAMETERS}
    risk_flags = []
    if constrained["parameters"]["use_grid"]:
        risk_flags.append("grid_enabled")
    if constrained["parameters"]["use_martingale"]:
        risk_flags.append("martingale_enabled")
    if constrained["parameters"]["SL"] <= 0:
        risk_flags.append("no_stop")
    if constrained["parameters"]["risk_percent"] > 5:
        risk_flags.append("high_risk_percent")
    constrained["risk_flags"] = risk_flags
    constrained["constraints_applied"] = True
    return constrained


def generate_candidates(seed: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Generate finite, traceable strategy candidates from one seed."""

    normalized_seed = _validate_seed(seed or DEFAULT_SEED)
    generated_at = _utc_now()
    candidates: list[dict[str, Any]] = []
    for mutation in mutate_parameters(normalized_seed):
        candidate = {
            "candidate_id": _candidate_id(
                normalized_seed["seed_id"],
                mutation["mutation_origin"],
                mutation["parameters"],
            ),
            "seed_id": normalized_seed["seed_id"],
            "seed_trace": {
                "source_seed_id": normalized_seed["seed_id"],
                "strategy_family": normalized_seed.get("strategy_family", "unknown"),
                "symbol": normalized_seed.get("symbol", "XAUUSD"),
                "timeframe": normalized_seed.get("timeframe", "M5"),
            },
            "mutation_origin": mutation["mutation_origin"],
            "changed_parameters": mutation["changed_parameters"],
            "parameters": mutation["parameters"],
            "created_at": generated_at,
            "mt5_real_run": False,
            "backtest_run": False,
        }
        candidates.append(apply_constraints(candidate))
    return candidates


def save_candidates(candidates: list[dict[str, Any]], root: Path | str = "candidates") -> CandidateGenerationResult:
    """Persist generated candidates and the public generation log."""

    candidates_root = Path(root)
    project_root = candidates_root.parent if candidates_root.name == "candidates" else Path(".")
    report_root = project_root / "reports" / "public"
    candidates_root.mkdir(parents=True, exist_ok=True)
    report_root.mkdir(parents=True, exist_ok=True)

    files: list[str] = []
    for candidate in candidates:
        path = candidates_root / f"{candidate['candidate_id']}.json"
        path.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        files.append(str(path))

    log = {
        "status": "candidate_generation_completed",
        "candidate_count": len(candidates),
        "allowed_parameters": ALLOWED_PARAMETERS,
        "mt5_real_run": False,
        "backtest_run": False,
        "loop_execution": False,
        "candidates": [
            {
                "candidate_id": candidate["candidate_id"],
                "seed_id": candidate["seed_id"],
                "mutation_origin": candidate["mutation_origin"],
                "risk_flags": candidate["risk_flags"],
            }
            for candidate in candidates
        ],
    }
    log_path = report_root / "candidate_generation_log.json"
    log_path.write_text(json.dumps(log, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return CandidateGenerationResult(candidates=candidates, files=files, log_path=str(log_path))


def list_candidates(root: Path | str = "candidates") -> list[dict[str, Any]]:
    candidates_root = Path(root)
    loaded: list[dict[str, Any]] = []
    if not candidates_root.exists():
        return loaded
    for path in sorted(candidates_root.glob("*.json")):
        loaded.append(json.loads(path.read_text(encoding="utf-8")))
    return loaded
