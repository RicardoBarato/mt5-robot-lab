"""Parse MT5 Strategy Tester reports into normalized smoke metrics."""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class BacktestMetrics:
    profit: float
    drawdown: float
    trades: int
    winrate: float
    profit_factor: float

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


def empty_smoke_metrics() -> BacktestMetrics:
    return BacktestMetrics(profit=0.0, drawdown=0.0, trades=0, winrate=0.0, profit_factor=0.0)


def _parse_number(value: str) -> float:
    cleaned = value.strip().replace("\u00a0", " ").replace(" ", "")
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    return float(cleaned)


def _first_number_after(labels: list[str], text: str) -> float | None:
    for label in labels:
        pattern = re.compile(rf"{re.escape(label)}\s*[:=]?\s*(-?\d[\d\s.,]*)", re.IGNORECASE)
        match = pattern.search(text)
        if match:
            return _parse_number(match.group(1))
    return None


def parse_backtest_report_text(text: str) -> BacktestMetrics:
    """Extract the standard MVP-004 metrics from a text or HTML report body."""

    profit = _first_number_after(["Total Net Profit", "Net Profit", "Profit"], text)
    drawdown = _first_number_after(
        ["Equity Drawdown Maximal", "Balance Drawdown Maximal", "Maximal Drawdown", "Drawdown"],
        text,
    )
    trades = _first_number_after(["Total Trades", "Trades"], text)
    winrate = _first_number_after(["Win Rate", "Winrate", "Profit Trades"], text)
    profit_factor = _first_number_after(["Profit Factor"], text)

    return BacktestMetrics(
        profit=profit or 0.0,
        drawdown=drawdown or 0.0,
        trades=int(trades or 0),
        winrate=winrate or 0.0,
        profit_factor=profit_factor or 0.0,
    )


def parse_backtest_report_file(path: str) -> BacktestMetrics:
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        return parse_backtest_report_text(handle.read())
