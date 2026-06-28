"""Tournament configuration model and safe public summaries."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.intelligence_modes import INTELLIGENCE_MODES
from app.core.symbol_mapping import TIMEFRAME_MINUTES


VALID_OUTPUT_FORMATS = {"csv", "md", "xlsx"}


@dataclass(frozen=True)
class TournamentConfig:
    lab_id: str
    lab_name: str
    lab_path: str
    requested_symbol: str
    broker_symbol: str
    timeframe: str
    timeframe_minutes: int
    backtest_years: int
    initial_balance_usd: int
    max_backtests: int
    champion_count: int
    intelligence_mode: str
    output_formats: list[str] = field(default_factory=list)
    mt5_terminal_path: str = ""
    mt5_metaeditor_path: str = ""
    codex_enabled: bool = False
    codex_authorized: bool = False
    created_at: str = ""
    updated_at: str = ""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def timeframe_to_minutes(timeframe: str) -> int:
    if timeframe not in TIMEFRAME_MINUTES:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    return TIMEFRAME_MINUTES[timeframe]


def default_tournament_config() -> TournamentConfig:
    now = utc_now()
    return TournamentConfig(
        lab_id="ea-xau",
        lab_name="XAU Robot Lab",
        lab_path="E:\\ea-xau",
        requested_symbol="XAUUSD",
        broker_symbol="",
        timeframe="M5",
        timeframe_minutes=5,
        backtest_years=2,
        initial_balance_usd=10000,
        max_backtests=100,
        champion_count=10,
        intelligence_mode="local_auto",
        output_formats=["csv", "md", "xlsx"],
        codex_enabled=False,
        codex_authorized=False,
        created_at=now,
        updated_at=now,
    )


def validate_tournament_config(config: TournamentConfig) -> None:
    if config.backtest_years <= 0:
        raise ValueError("backtest_years must be > 0")
    if config.initial_balance_usd <= 0:
        raise ValueError("initial_balance_usd must be > 0")
    if config.max_backtests <= 0:
        raise ValueError("max_backtests must be > 0")
    if config.champion_count <= 0:
        raise ValueError("champion_count must be > 0")
    if config.champion_count > config.max_backtests:
        raise ValueError("champion_count must be <= max_backtests")
    if not config.requested_symbol.strip():
        raise ValueError("requested_symbol must not be empty")
    if config.timeframe not in TIMEFRAME_MINUTES:
        raise ValueError("timeframe is not supported")
    if config.timeframe_minutes != timeframe_to_minutes(config.timeframe):
        raise ValueError("timeframe_minutes does not match timeframe")
    if config.intelligence_mode not in INTELLIGENCE_MODES:
        raise ValueError("intelligence_mode is not supported")
    unknown_formats = set(config.output_formats) - VALID_OUTPUT_FORMATS
    if unknown_formats:
        raise ValueError(f"Unsupported output_formats: {sorted(unknown_formats)}")


def normalize_tournament_config(config: TournamentConfig) -> TournamentConfig:
    payload = to_dict(config)
    payload["requested_symbol"] = str(payload["requested_symbol"]).strip().upper()
    payload["broker_symbol"] = str(payload.get("broker_symbol", "")).strip()
    payload["timeframe"] = str(payload["timeframe"]).strip().upper()
    payload["timeframe_minutes"] = timeframe_to_minutes(payload["timeframe"])
    payload["output_formats"] = sorted(set(payload.get("output_formats") or []))
    payload["updated_at"] = utc_now()
    normalized = from_dict(payload)
    validate_tournament_config(normalized)
    return normalized


def to_dict(config: TournamentConfig) -> dict[str, Any]:
    return asdict(config)


def from_dict(data: dict[str, Any]) -> TournamentConfig:
    baseline = to_dict(default_tournament_config())
    baseline.update(data)
    return TournamentConfig(**baseline)


def save_local_config(config: TournamentConfig, path: Path) -> Path:
    normalized = normalize_tournament_config(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_dict(normalized), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_local_config(path: Path) -> TournamentConfig:
    return normalize_tournament_config(from_dict(json.loads(path.read_text(encoding="utf-8"))))


def make_public_summary(config: TournamentConfig) -> dict[str, Any]:
    normalized = normalize_tournament_config(config)
    return {
        "lab_id": normalized.lab_id,
        "lab_name": normalized.lab_name,
        "requested_symbol": normalized.requested_symbol,
        "broker_symbol": normalized.broker_symbol,
        "timeframe": normalized.timeframe,
        "timeframe_minutes": normalized.timeframe_minutes,
        "backtest_years": normalized.backtest_years,
        "initial_balance_usd": normalized.initial_balance_usd,
        "max_backtests": normalized.max_backtests,
        "champion_count": normalized.champion_count,
        "intelligence_mode": normalized.intelligence_mode,
        "output_formats": normalized.output_formats,
        "codex_enabled": normalized.codex_enabled,
        "codex_authorized": normalized.codex_authorized,
        "mt5_real_run": False,
        "backtest_real_run": False,
        "tournament_100_run": False,
    }


def write_public_preview(config: TournamentConfig, output_dir: Path) -> dict[str, Path]:
    summary = make_public_summary(config)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "tournament_config_preview.json"
    md_path = output_dir / "tournament_config_preview.md"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# Tournament Config Preview", ""]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("No real MT5 run, real backtest, account, broker server, password or token is included.")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": json_path, "md": md_path}
