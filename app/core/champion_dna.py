"""Champion DNA v2 schema and artifact helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.candidate_generator import DEFAULT_SEED
from app.core.symbol_mapping import TIMEFRAME_MINUTES


PRIVATE_SUMMARY_TERMS = ["password", "senha", "token", "secret", "api_key", "account", "broker server", "C:\\"]


@dataclass(frozen=True)
class ChampionDNA:
    champion_id: str
    candidate_id: str
    rank: int
    lab_id: str
    lab_name: str
    source_seed_id: str
    source_seed_file: str
    source_mq5_hash: str
    candidate_file: str
    candidate_hash: str
    requested_symbol: str
    broker_symbol: str
    timeframe: str
    timeframe_minutes: int
    backtest_years: float
    initial_balance_usd: float
    final_balance_usd: float
    net_profit_usd: float
    max_drawdown_usd: float
    max_drawdown_pct: float
    profit_factor: float
    expected_payoff: float
    total_trades: int
    win_rate: float
    largest_loss_streak: int
    risk_profile: str
    risk_mode: str
    max_drawdown_tolerated_pct: float
    ranking_profile: str
    ranking_reason: str
    martingale_used: bool
    grid_used: bool
    no_stop_used: bool
    risk_flags: list[str]
    intelligence_mode: str
    codex_used: bool
    codex_authorized: bool
    mutation_mode: str
    parameter_changes: list[dict[str, Any]] = field(default_factory=list)
    code_changes_summary: str = ""
    generated_from_candidate_id: str = ""
    generation_number: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat())
    test_run_id: str = ""
    report_path: str = ""
    notes: str = ""
    status: str = "smoke_or_dry_run"
    mt5_real_run: bool = False
    backtest_real_run: bool = False


def hash_source_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _risk_impact(parameter: str, before: Any, after: Any) -> str:
    if before == after:
        return "neutral"
    if parameter in {"use_grid", "use_martingale"}:
        return "risk_increase" if bool(after) else "risk_decrease"
    if parameter == "SL":
        try:
            if float(after) <= 0:
                return "risk_increase"
            return "risk_decrease" if float(after) > float(before) else "risk_increase"
        except (TypeError, ValueError):
            return "unknown"
    if parameter == "risk_percent":
        return "risk_increase" if float(after) > float(before) else "risk_decrease"
    if parameter in {"TP_R", "lot_multiplier"}:
        return "profit_aggressive" if float(after) > float(before) else "risk_decrease"
    if parameter in {"break_even", "trailing_stop", "use_session_filter"}:
        return "risk_decrease" if bool(after) else "risk_increase"
    return "neutral"


def parameter_diff(original_params: dict[str, Any], final_params: dict[str, Any]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for name in sorted(set(original_params) | set(final_params)):
        before = original_params.get(name)
        after = final_params.get(name)
        if before == after:
            continue
        if before is None:
            change_type = "added"
        elif after is None:
            change_type = "removed"
        else:
            change_type = "modified"
        changes.append(
            {
                "parameter": name,
                "before": before,
                "after": after,
                "change_type": change_type,
                "risk_impact": _risk_impact(name, before, after),
            }
        )
    return changes


def _risk_mode(profile_id: str) -> str:
    return "wild" if profile_id == "wild" else "controlled_risk"


def _ranking_profile(profile_id: str) -> str:
    return "wild_profit" if profile_id == "wild" else "controlled_risk"


def _ranking_reason(profile: dict[str, Any]) -> str:
    profile_id = profile.get("profile_id", "controlled_risk")
    allowed = bool(profile.get("profile_allowed", True))
    max_dd = profile.get("max_drawdown_tolerated", profile.get("max_drawdown_tolerated_pct", 20.0))
    rejections = profile.get("profile_rejection_reasons") or profile.get("rejected_by_profile_reason") or []
    if profile_id == "wild":
        return f"Wild Mode accepted this candidate because profit ranked highest and max drawdown tolerance was {max_dd}%."
    if allowed:
        return f"Controlled Risk accepted this candidate inside {max_dd}% max drawdown tolerance with no disallowed risk flags."
    return (
        "Controlled Risk rejected or downgraded this candidate because "
        f"{', '.join(rejections) if rejections else 'profile constraints were not met'}."
    )


def create_champion_dna(
    candidate: dict[str, Any],
    metrics: dict[str, Any],
    config: dict[str, Any],
    risk_profile: dict[str, Any],
) -> ChampionDNA:
    final_params = candidate.get("parameters", {})
    original_params = config.get("source_parameters") or DEFAULT_SEED["parameters"]
    risk_flags = list(candidate.get("risk_flags") or risk_profile.get("risk_flags") or [])
    requested_symbol = config.get("requested_symbol") or candidate.get("requested_symbol") or config.get("symbol", "XAUUSD")
    timeframe = config.get("timeframe") or candidate.get("timeframe") or "M5"
    candidate_payload = json.dumps(candidate, sort_keys=True)
    source_text = config.get("source_mq5_text", "")
    source_hash = hash_source_text(source_text) if source_text else hash_source_text("source_unavailable_public_smoke")
    candidate_hash = hash_source_text(candidate_payload)
    candidate_id = candidate.get("candidate_id", "unknown_candidate")
    profile_id = risk_profile.get("profile_id") or risk_profile.get("risk_profile") or "controlled_risk"
    max_dd_tolerated = float(risk_profile.get("max_drawdown_tolerated_pct", risk_profile.get("max_drawdown_tolerated", 20.0)))
    initial_balance = float(config.get("initial_balance_usd", 10000.0))
    net_profit = float(metrics.get("net_profit_usd", metrics.get("profit", 0.0)) or 0.0)
    final_balance = float(metrics.get("final_balance_usd", initial_balance + net_profit) or initial_balance + net_profit)
    total_trades = int(metrics.get("total_trades", metrics.get("trades", 0)) or 0)
    win_rate = float(metrics.get("win_rate", metrics.get("winrate", 0.0)) or 0.0)

    return ChampionDNA(
        champion_id=f"champion_{candidate_id}_{_risk_mode(profile_id)}",
        candidate_id=candidate_id,
        rank=int(candidate.get("rank", risk_profile.get("profile_rank", 1)) or 1),
        lab_id=config.get("lab_id", "ea-xau"),
        lab_name=config.get("lab_name", "XAU Robot Lab"),
        source_seed_id=candidate.get("seed_id", config.get("source_seed_id", DEFAULT_SEED["seed_id"])),
        source_seed_file=config.get("source_seed_file", "embedded_default_seed"),
        source_mq5_hash=source_hash,
        candidate_file=config.get("candidate_file", f"candidates/{candidate_id}.json"),
        candidate_hash=candidate_hash,
        requested_symbol=requested_symbol,
        broker_symbol=config.get("broker_symbol", requested_symbol),
        timeframe=timeframe,
        timeframe_minutes=int(config.get("timeframe_minutes", TIMEFRAME_MINUTES.get(timeframe, 5))),
        backtest_years=float(config.get("backtest_years", 0.0)),
        initial_balance_usd=initial_balance,
        final_balance_usd=final_balance,
        net_profit_usd=net_profit,
        max_drawdown_usd=float(metrics.get("max_drawdown_usd", metrics.get("drawdown", 0.0)) or 0.0),
        max_drawdown_pct=float(metrics.get("max_drawdown_pct", 0.0) or 0.0),
        profit_factor=float(metrics.get("profit_factor", 0.0) or 0.0),
        expected_payoff=float(metrics.get("expected_payoff", 0.0) or 0.0),
        total_trades=total_trades,
        win_rate=win_rate,
        largest_loss_streak=int(metrics.get("largest_loss_streak", 0) or 0),
        risk_profile=profile_id,
        risk_mode=_risk_mode(profile_id),
        max_drawdown_tolerated_pct=max_dd_tolerated,
        ranking_profile=_ranking_profile(profile_id),
        ranking_reason=risk_profile.get("ranking_reason") or _ranking_reason(risk_profile),
        martingale_used="martingale_enabled" in risk_flags or bool(final_params.get("use_martingale", False)),
        grid_used="grid_enabled" in risk_flags or bool(final_params.get("use_grid", False)),
        no_stop_used="no_stop" in risk_flags or float(final_params.get("SL", 0) or 0) <= 0,
        risk_flags=risk_flags,
        intelligence_mode=config.get("intelligence_mode", "local_auto"),
        codex_used=bool(config.get("codex_used", False)),
        codex_authorized=bool(config.get("codex_authorized", False)),
        mutation_mode=config.get("mutation_mode", "programmatic_local_mutation"),
        parameter_changes=parameter_diff(original_params, final_params),
        code_changes_summary=config.get("code_changes_summary", "No source code copied; smoke candidate parameters only."),
        generated_from_candidate_id=candidate.get("generated_from_candidate_id", candidate_id),
        generation_number=int(config.get("generation_number", 1)),
        test_run_id=config.get("test_run_id", "smoke_dry_run"),
        report_path=config.get("report_path", "reports/public/tournament_summary.md"),
        notes=config.get("notes", "Champion DNA v2 sample generated from smoke or dry-run data."),
        status=config.get("status", "smoke_or_dry_run"),
        mt5_real_run=bool(config.get("mt5_real_run", False)),
        backtest_real_run=bool(config.get("backtest_real_run", False)),
    )


def validate_champion_dna(dna: ChampionDNA | dict[str, Any]) -> None:
    payload = asdict(dna) if isinstance(dna, ChampionDNA) else dna
    required = set(ChampionDNA.__dataclass_fields__)
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"Champion DNA missing fields: {missing}")
    if payload["risk_mode"] not in {"wild", "controlled_risk"}:
        raise ValueError("risk_mode must be wild or controlled_risk")
    if payload["max_drawdown_tolerated_pct"] not in {20.0, 100.0}:
        raise ValueError("max_drawdown_tolerated_pct must be 20.0 or 100.0 for MVP-008")
    if payload["mt5_real_run"] or payload["backtest_real_run"]:
        raise ValueError("MVP-008 sample DNA must not claim real MT5/backtest execution")
    summary = make_public_champion_summary(payload)
    lowered = summary.lower()
    if any(term.lower() in lowered for term in PRIVATE_SUMMARY_TERMS):
        raise ValueError("Public summary contains a private or sensitive term")


def summarize_adjustments(dna: ChampionDNA | dict[str, Any]) -> str:
    payload = asdict(dna) if isinstance(dna, ChampionDNA) else dna
    changes = payload.get("parameter_changes", [])
    if not changes:
        return "No parameter changes were recorded."
    parts = [f"{item['parameter']}: {item.get('before')} -> {item.get('after')} ({item.get('risk_impact')})" for item in changes]
    return "; ".join(parts)


def make_public_champion_summary(dna: ChampionDNA | dict[str, Any]) -> str:
    payload = asdict(dna) if isinstance(dna, ChampionDNA) else dna
    lines = [
        "# Champion DNA v2 Public Summary",
        "",
        f"- Champion ID: {payload['champion_id']}",
        f"- Candidate ID: {payload['candidate_id']}",
        f"- Rank: {payload['rank']}",
        f"- Lab: {payload['lab_name']} ({payload['lab_id']})",
        f"- Symbol/timeframe: {payload['broker_symbol']} {payload['timeframe']}",
        f"- Risk mode: {payload['risk_mode']}",
        f"- Max drawdown tolerated: {payload['max_drawdown_tolerated_pct']}%",
        f"- Net profit USD: {payload['net_profit_usd']}",
        f"- Max drawdown pct: {payload['max_drawdown_pct']}",
        f"- Profit factor: {payload['profit_factor']}",
        f"- Total trades: {payload['total_trades']}",
        f"- Risk flags: {', '.join(payload['risk_flags']) if payload['risk_flags'] else 'none'}",
        f"- Ranking reason: {payload['ranking_reason']}",
        f"- Adjustments: {summarize_adjustments(payload)}",
        "",
        "This is a public-safe research summary. It is not a live trading approval or financial recommendation.",
    ]
    return "\n".join(lines) + "\n"


def save_champion_dna(dna: ChampionDNA, output_dir: Path) -> dict[str, Path]:
    validate_champion_dna(dna)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = asdict(dna)
    dna_path = output_dir / "sample_champion_dna_v2.json"
    summary_path = output_dir / "sample_champion_dna_v2.md"
    dna_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.write_text(make_public_champion_summary(dna), encoding="utf-8")
    return {"champion_dna_v2": dna_path, "public_summary": summary_path}


def load_champion_dna(path: Path) -> ChampionDNA:
    payload = json.loads(path.read_text(encoding="utf-8"))
    dna = ChampionDNA(**payload)
    validate_champion_dna(dna)
    return dna


def sample_champion_dna() -> ChampionDNA:
    candidate = {
        "candidate_id": "sample_xau_candidate_001",
        "seed_id": DEFAULT_SEED["seed_id"],
        "rank": 1,
        "parameters": {
            **DEFAULT_SEED["parameters"],
            "ATR_period": 21,
            "ADX_min": 18,
            "TP_R": 3.5,
            "use_grid": True,
            "use_martingale": True,
        },
        "risk_flags": ["grid_enabled", "martingale_enabled"],
    }
    metrics = {
        "net_profit_usd": 1250.0,
        "final_balance_usd": 11250.0,
        "max_drawdown_usd": 700.0,
        "max_drawdown_pct": 7.0,
        "profit_factor": 1.35,
        "expected_payoff": 12.5,
        "total_trades": 100,
        "win_rate": 42.0,
        "largest_loss_streak": 6,
    }
    config = {
        "lab_id": "ea-xau",
        "lab_name": "XAU Robot Lab",
        "requested_symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "timeframe": "M5",
        "backtest_years": 2.0,
        "initial_balance_usd": 10000.0,
        "test_run_id": "sample_run",
        "report_path": "reports/public/mt5_robot_lab_sample_summary.md",
        "notes": "Bootstrap sample.",
    }
    risk_profile = {
        "profile_id": "wild",
        "profile_rank": 1,
        "max_drawdown_tolerated": 100.0,
        "profile_allowed": True,
    }
    return create_champion_dna(candidate, metrics, config, risk_profile)


def parameter_diff_markdown(dna: ChampionDNA) -> str:
    lines = ["# Parameter Diff", ""]
    for change in dna.parameter_changes:
        lines.append(
            f"- {change['parameter']}: {change.get('before')} -> {change.get('after')} "
            f"({change['change_type']}, {change['risk_impact']})"
        )
    return "\n".join(lines) + "\n"


def write_champion_artifacts(dna: ChampionDNA, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    dna_path = output_dir / "champion_dna.json"
    metrics_path = output_dir / "metrics.json"
    diff_path = output_dir / "parameter_diff.md"
    source_hashes_path = output_dir / "source_hashes.json"
    summary_path = output_dir / "public_summary.md"
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
    source_hashes = {"source_mq5_hash": dna.source_mq5_hash, "candidate_hash": dna.candidate_hash}
    source_hashes_path.write_text(json.dumps(source_hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.write_text(make_public_champion_summary(dna), encoding="utf-8")
    return {
        "champion_dna": dna_path,
        "metrics": metrics_path,
        "parameter_diff": diff_path,
        "source_hashes": source_hashes_path,
        "public_summary": summary_path,
    }
