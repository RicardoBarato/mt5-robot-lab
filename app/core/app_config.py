"""Application configuration loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AppConfig:
    product_name: str
    default_lab: str
    default_lab_path: str
    default_symbol: str
    default_timeframe: str
    default_backtest_years: int
    default_initial_balance_usd: int
    default_max_backtests: int
    default_champion_count: int
    default_intelligence_mode: str
    supported_intelligence_modes: list[str]
    supported_timeframes: list[str]
    output_formats: list[str]
    mt5_installer_bundled: bool
    codex_required: bool
    cli_required_for_end_user: bool


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_app_config(path: Path) -> AppConfig:
    payload = load_json(path)
    return AppConfig(**payload)


def validate_app_config(config: AppConfig) -> None:
    if config.product_name != "MT5 Robot Lab":
        raise ValueError("product_name must be MT5 Robot Lab")
    if config.default_symbol != "XAUUSD":
        raise ValueError("default_symbol must be XAUUSD")
    if config.default_timeframe != "M5":
        raise ValueError("default_timeframe must be M5")
    if config.default_initial_balance_usd != 10000:
        raise ValueError("default_initial_balance_usd must be 10000")
    if config.default_max_backtests != 100:
        raise ValueError("default_max_backtests must be 100")
    if config.mt5_installer_bundled:
        raise ValueError("MT5 installer must not be bundled")
    if config.codex_required:
        raise ValueError("Codex must not be required")
    if config.cli_required_for_end_user:
        raise ValueError("CLI must not be required for end users")
