"""Public report export helpers."""

from __future__ import annotations

import csv
from dataclasses import asdict
from pathlib import Path

from app.core.champion_dna import ChampionDNA, sample_champion_dna


EXPORT_COLUMNS = [
    "rank",
    "candidate_id",
    "lab_id",
    "seed_family",
    "symbol",
    "broker_symbol",
    "timeframe",
    "years_tested",
    "initial_balance_usd",
    "net_profit_usd",
    "final_balance_usd",
    "max_drawdown_pct",
    "profit_factor",
    "total_trades",
    "win_rate",
    "martingale_used",
    "grid_used",
    "no_stop_used",
    "intelligence_mode",
    "source_file",
    "report_path",
    "notes",
]


def _row(dna: ChampionDNA) -> dict[str, object]:
    payload = asdict(dna)
    payload["source_file"] = payload.pop("source_mq5")
    return {column: payload.get(column, "") for column in EXPORT_COLUMNS}


def export_csv(rows: list[ChampionDNA], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for item in rows:
            writer.writerow(_row(item))
    return path


def export_markdown(rows: list[ChampionDNA], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# MT5 Robot Lab Sample Summary", "", "| " + " | ".join(EXPORT_COLUMNS) + " |"]
    lines.append("| " + " | ".join(["---"] * len(EXPORT_COLUMNS)) + " |")
    for item in rows:
        row = _row(item)
        lines.append("| " + " | ".join(str(row[column]) for column in EXPORT_COLUMNS) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def export_xlsx_if_available(rows: list[ChampionDNA], path: Path) -> Path | None:
    try:
        from openpyxl import Workbook  # type: ignore
    except ImportError:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Summary"
    sheet.append(EXPORT_COLUMNS)
    for item in rows:
        row = _row(item)
        sheet.append([row[column] for column in EXPORT_COLUMNS])
    workbook.save(path)
    return path


def export_sample_summary(output_dir: Path) -> dict[str, Path | None]:
    rows = [sample_champion_dna()]
    return {
        "csv": export_csv(rows, output_dir / "mt5_robot_lab_sample_summary.csv"),
        "md": export_markdown(rows, output_dir / "mt5_robot_lab_sample_summary.md"),
        "xlsx": export_xlsx_if_available(rows, output_dir / "mt5_robot_lab_sample_summary.xlsx"),
    }
