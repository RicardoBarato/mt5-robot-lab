"""Future online leaderboard schema for public-safe submissions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_ENTRY_FIELDS = {
    "entry_id",
    "submission_id",
    "champion_id",
    "user_display_name",
    "team_name",
    "country",
    "product_version",
    "package_version",
    "asset",
    "requested_symbol",
    "broker_symbol",
    "timeframe",
    "timeframe_minutes",
    "backtest_years",
    "initial_balance_usd",
    "risk_profile",
    "risk_mode",
    "max_drawdown_tolerated_pct",
    "ranking_mode",
    "net_profit_usd",
    "final_balance_usd",
    "max_drawdown_pct",
    "profit_factor",
    "total_trades",
    "win_rate",
    "martingale_used",
    "grid_used",
    "no_stop_used",
    "mt5_real_run",
    "backtest_real_run",
    "validation_status",
    "upload_ready",
    "created_at",
    "public_summary_path",
}

FORBIDDEN_PUBLIC_TEXT = ["password", "senha", "token", "secret", "api_key", "broker_password"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def default_leaderboard_categories() -> dict[str, list[str]]:
    return {
        "asset_symbol": ["XAUUSD", "USTEC", "US30", "EURUSD", "GBPUSD", "BTCUSD", "manual_broker_symbol"],
        "timeframe": ["M1", "M5", "M15", "M30", "H1", "H4", "D1"],
        "backtest_window": ["6_months", "1_year", "2_years", "5_years", "custom"],
        "initial_balance": ["1000", "10000", "50000", "custom"],
        "risk_profile": ["Wild Mode", "Controlled Risk Mode", "max DD 10%", "max DD 20%", "max DD 30%", "max DD 50%", "max DD 100%"],
        "ranking_mode": ["highest_net_profit", "highest_profit_factor", "lowest_drawdown", "profit_per_drawdown", "most_stable"],
    }


def _asset_from_symbol(symbol: str) -> str:
    upper = symbol.upper()
    if "XAU" in upper or "GOLD" in upper:
        return "XAUUSD"
    if upper in {"USTEC", "NAS100", "US100"} or "USTEC" in upper:
        return "USTEC"
    if upper in {"US30", "DJ30"} or "US30" in upper:
        return "US30"
    if "BTC" in upper:
        return "BTCUSD"
    if upper in {"EURUSD", "GBPUSD"}:
        return upper
    return "manual_broker_symbol"


def build_leaderboard_entry(submission_manifest: dict[str, Any]) -> dict[str, Any]:
    net_profit = float(submission_manifest.get("net_profit_usd", 0) or 0)
    initial_balance = float(submission_manifest.get("initial_balance_usd", 0) or 0)
    broker_symbol = submission_manifest.get("broker_symbol", submission_manifest.get("requested_symbol", "XAUUSD"))
    entry = {
        "entry_id": f"entry_{submission_manifest.get('submission_id', 'sample')}",
        "submission_id": submission_manifest.get("submission_id", "sample_submission"),
        "champion_id": submission_manifest.get("champion_id", "sample_champion"),
        "user_display_name": submission_manifest.get("user_display_name", "sample_user"),
        "team_name": submission_manifest.get("team_name", "sample_team"),
        "country": submission_manifest.get("country", "BR"),
        "product_version": submission_manifest.get("app_version", "mvp-010"),
        "package_version": submission_manifest.get("package_version", "1.0"),
        "asset": _asset_from_symbol(str(broker_symbol)),
        "requested_symbol": submission_manifest.get("requested_symbol", broker_symbol),
        "broker_symbol": broker_symbol,
        "timeframe": submission_manifest.get("timeframe", "M5"),
        "timeframe_minutes": int(submission_manifest.get("timeframe_minutes", 5) or 5),
        "backtest_years": float(submission_manifest.get("backtest_years", 0) or 0),
        "initial_balance_usd": initial_balance,
        "risk_profile": submission_manifest.get("risk_profile", "wild"),
        "risk_mode": submission_manifest.get("risk_mode", "wild"),
        "max_drawdown_tolerated_pct": float(submission_manifest.get("max_drawdown_tolerated_pct", 100.0) or 100.0),
        "ranking_mode": submission_manifest.get("ranking_mode", "highest_net_profit"),
        "net_profit_usd": net_profit,
        "final_balance_usd": float(submission_manifest.get("final_balance_usd", initial_balance + net_profit) or initial_balance + net_profit),
        "max_drawdown_pct": float(submission_manifest.get("max_drawdown_pct", 0) or 0),
        "profit_factor": float(submission_manifest.get("profit_factor", 0) or 0),
        "total_trades": int(submission_manifest.get("total_trades", 0) or 0),
        "win_rate": float(submission_manifest.get("win_rate", 0) or 0),
        "martingale_used": bool(submission_manifest.get("martingale_used", False)),
        "grid_used": bool(submission_manifest.get("grid_used", False)),
        "no_stop_used": bool(submission_manifest.get("no_stop_used", False)),
        "mt5_real_run": bool(submission_manifest.get("mt5_real_run", False)),
        "backtest_real_run": bool(submission_manifest.get("backtest_real_run", False)),
        "validation_status": submission_manifest.get("validation_status", "sample_not_real_backtest"),
        "upload_ready": bool(submission_manifest.get("upload_ready", False)),
        "created_at": submission_manifest.get("created_at", _utc_now()),
        "public_summary_path": submission_manifest.get("public_summary_path", "reports/public/leaderboard_sample.md"),
    }
    return entry


def validate_leaderboard_entry(entry: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_ENTRY_FIELDS - set(entry))
    if missing:
        raise ValueError(f"Leaderboard entry missing fields: {missing}")
    if entry["timeframe"] not in default_leaderboard_categories()["timeframe"]:
        raise ValueError("Unsupported timeframe")
    if not isinstance(entry["upload_ready"], bool):
        raise ValueError("upload_ready must be boolean")
    if entry["validation_status"] == "":
        raise ValueError("validation_status is required")
    public_text = json.dumps(entry, sort_keys=True).lower()
    for term in FORBIDDEN_PUBLIC_TEXT:
        if term in public_text:
            raise ValueError("Leaderboard entry contains sensitive text")


def category_key(entry: dict[str, Any]) -> str:
    validate_leaderboard_entry(entry)
    balance = int(float(entry["initial_balance_usd"]))
    return "|".join(
        [
            str(entry["asset"]),
            str(entry["timeframe"]),
            f"{entry['backtest_years']}y",
            str(balance),
            str(entry["risk_mode"]),
            f"dd{entry['max_drawdown_tolerated_pct']}",
        ]
    )


def rank_entries(entries: list[dict[str, Any]], ranking_mode: str) -> list[dict[str, Any]]:
    for entry in entries:
        validate_leaderboard_entry(entry)
    if ranking_mode == "highest_net_profit":
        ranked = sorted(entries, key=lambda item: float(item["net_profit_usd"]), reverse=True)
    elif ranking_mode == "highest_profit_factor":
        ranked = sorted(entries, key=lambda item: float(item["profit_factor"]), reverse=True)
    elif ranking_mode == "lowest_drawdown":
        ranked = sorted(entries, key=lambda item: float(item["max_drawdown_pct"]))
    elif ranking_mode == "profit_per_drawdown":
        ranked = sorted(entries, key=lambda item: float(item["net_profit_usd"]) / max(float(item["max_drawdown_pct"]), 0.01), reverse=True)
    elif ranking_mode == "most_stable":
        ranked = sorted(entries, key=lambda item: (float(item["profit_factor"]), -float(item["max_drawdown_pct"]), int(item["total_trades"])), reverse=True)
    else:
        raise ValueError(f"Unsupported ranking mode: {ranking_mode}")
    output = []
    for index, entry in enumerate(ranked, start=1):
        row = dict(entry)
        row["leaderboard_rank"] = index
        row["ranking_mode"] = ranking_mode
        row["category_key"] = category_key(row)
        output.append(row)
    return output


def _sample_manifest() -> dict[str, Any]:
    return {
        "submission_id": "submission_sample_leaderboard",
        "champion_id": "champion_sample_xau_candidate_001_wild",
        "candidate_id": "sample_xau_candidate_001",
        "app_version": "mvp-010",
        "package_version": "1.0",
        "requested_symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "timeframe": "M5",
        "timeframe_minutes": 5,
        "backtest_years": 2.0,
        "initial_balance_usd": 10000.0,
        "risk_profile": "wild",
        "risk_mode": "wild",
        "max_drawdown_tolerated_pct": 100.0,
        "net_profit_usd": 1250.0,
        "max_drawdown_pct": 7.0,
        "profit_factor": 1.35,
        "total_trades": 100,
        "win_rate": 42.0,
        "mt5_real_run": False,
        "backtest_real_run": False,
        "validation_status": "sample_not_real_backtest",
        "upload_ready": False,
        "created_at": _utc_now(),
        "user_display_name": "sample_user",
        "team_name": "sample_team",
        "country": "BR",
    }


def _leaderboard_markdown(entry: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# MT5 Robot Lab Rankings Sample",
            "",
            "- Status: sample_not_real_backtest",
            f"- Entry ID: {entry['entry_id']}",
            f"- User: {entry['user_display_name']}",
            f"- Team: {entry['team_name']}",
            f"- Country: {entry['country']}",
            f"- Asset/timeframe: {entry['asset']} {entry['timeframe']}",
            f"- Risk mode: {entry['risk_mode']}",
            f"- Net profit USD: {entry['net_profit_usd']}",
            f"- Max drawdown pct: {entry['max_drawdown_pct']}",
            "- MT5 real run: false",
            "- Backtest real run: false",
            "- Upload ready: false",
            "",
            "This is a fictitious public-safe leaderboard sample. It is not a trading signal, recommendation or real account approval.",
        ]
    ) + "\n"


def make_public_leaderboard_sample(
    output_dir: Path | None = None,
    submission_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = build_leaderboard_entry(submission_manifest or _sample_manifest())
    validate_leaderboard_entry(entry)
    ranked = rank_entries([entry], "highest_net_profit")
    categories = default_leaderboard_categories()
    payload = {
        "status": "sample_not_real_backtest",
        "mt5_real_run": False,
        "backtest_real_run": False,
        "upload_ready": False,
        "leaderboard_created": False,
        "online_upload": False,
        "categories": categories,
        "entries": ranked,
    }
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "leaderboard_sample.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (output_dir / "leaderboard_sample.md").write_text(_leaderboard_markdown(ranked[0]), encoding="utf-8")
    return payload
