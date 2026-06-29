"""Conservative parser for explicitly provided MT5 Strategy Tester reports."""

from __future__ import annotations

import csv
import html
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.core.mt5_detection import redact_public_path


SUPPORTED_FORMATS = {".html", ".htm", ".xml", ".csv", ".json"}


@dataclass(frozen=True)
class ParsedMT5Report:
    parseable: bool
    source_format: str
    result_status: str
    total_trades: int | None
    net_profit: float | None
    gross_profit: float | None
    gross_loss: float | None
    max_drawdown: float | None
    initial_deposit: float | None
    symbol: str | None
    timeframe: str | None
    started_at: str | None
    ended_at: str | None
    warnings: list[str] = field(default_factory=list)
    source_path_sanitized: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _assert_allowed_path(path: Path, allowed_root: Path | None) -> None:
    if allowed_root is None:
        return
    path.resolve().relative_to(allowed_root.resolve())


def _empty_result(path: Path, status: str, warnings: list[str] | None = None) -> ParsedMT5Report:
    return ParsedMT5Report(
        parseable=False,
        source_format=path.suffix.lower().lstrip(".") or "unknown",
        result_status=status,
        total_trades=None,
        net_profit=None,
        gross_profit=None,
        gross_loss=None,
        max_drawdown=None,
        initial_deposit=None,
        symbol=None,
        timeframe=None,
        started_at=None,
        ended_at=None,
        warnings=warnings or [],
        source_path_sanitized=redact_public_path(path),
    )


def _parse_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("\u00a0", " ")
    if not text:
        return None
    cleaned = re.sub(r"[^\d,.\-]", "", text)
    if not cleaned or cleaned in {"-", ".", ","}:
        return None
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_int(value: Any) -> int | None:
    number = _parse_number(value)
    return int(number) if number is not None else None


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


KEY_ALIASES = {
    "result_status": "result_status",
    "status": "result_status",
    "total_trades": "total_trades",
    "trades": "total_trades",
    "net_profit": "net_profit",
    "total_net_profit": "net_profit",
    "profit": "net_profit",
    "gross_profit": "gross_profit",
    "gross_loss": "gross_loss",
    "max_drawdown": "max_drawdown",
    "maximal_drawdown": "max_drawdown",
    "equity_drawdown_maximal": "max_drawdown",
    "initial_deposit": "initial_deposit",
    "deposit": "initial_deposit",
    "symbol": "symbol",
    "timeframe": "timeframe",
    "period": "timeframe",
    "started_at": "started_at",
    "start_time": "started_at",
    "from_date": "started_at",
    "ended_at": "ended_at",
    "end_time": "ended_at",
    "to_date": "ended_at",
}


def _canonical_data(data: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in data.items():
        canonical = KEY_ALIASES.get(_normalize_key(str(key)))
        if canonical and result.get(canonical) in (None, ""):
            result[canonical] = value
    return result


def _fields_from_text(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
        elif "=" in line:
            key, value = line.split("=", 1)
        else:
            continue
        if KEY_ALIASES.get(_normalize_key(key)):
            data[key.strip()] = value.strip()
    return data


def _strip_html(text: str) -> str:
    unescaped = html.unescape(text)
    no_tags = re.sub(r"<[^>]+>", "\n", unescaped)
    return re.sub(r"\n{2,}", "\n", no_tags)


def _parse_html(path: Path) -> dict[str, Any]:
    return _fields_from_text(_strip_html(path.read_text(encoding="utf-8", errors="ignore")))


def _parse_xml(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    data: dict[str, Any] = {}
    for element in root.iter():
        tag = element.tag.split("}", 1)[-1]
        if len(element):
            continue
        text = (element.text or "").strip()
        if text:
            data[tag] = text
    return data


def _parse_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _parse_csv(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return dict(rows[0]) if rows else {}


def _build_result(path: Path, raw_data: dict[str, Any], warnings: list[str]) -> ParsedMT5Report:
    data = _canonical_data(raw_data)
    known_values = [value for value in data.values() if value not in (None, "")]
    parseable = bool(known_values)
    return ParsedMT5Report(
        parseable=parseable,
        source_format=path.suffix.lower().lstrip("."),
        result_status=str(data.get("result_status") or ("parsed" if parseable else "unsupported_format_or_missing_fields")),
        total_trades=_parse_int(data.get("total_trades")),
        net_profit=_parse_number(data.get("net_profit")),
        gross_profit=_parse_number(data.get("gross_profit")),
        gross_loss=_parse_number(data.get("gross_loss")),
        max_drawdown=_parse_number(data.get("max_drawdown")),
        initial_deposit=_parse_number(data.get("initial_deposit")),
        symbol=str(data["symbol"]) if data.get("symbol") else None,
        timeframe=str(data["timeframe"]) if data.get("timeframe") else None,
        started_at=str(data["started_at"]) if data.get("started_at") else None,
        ended_at=str(data["ended_at"]) if data.get("ended_at") else None,
        warnings=warnings,
        source_path_sanitized=redact_public_path(path),
    )


def parse_mt5_report(path: str | Path, *, allowed_root: str | Path | None = None) -> ParsedMT5Report:
    report_path = Path(path)
    root = Path(allowed_root) if allowed_root is not None else None
    try:
        _assert_allowed_path(report_path, root)
    except ValueError:
        return _empty_result(report_path, "path_outside_allowed_root", ["outside_allowed_root"])

    suffix = report_path.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        return _empty_result(report_path, "unsupported_format_or_missing_fields", ["unsupported_format"])
    if not report_path.exists() or not report_path.is_file():
        return _empty_result(report_path, "unsupported_format_or_missing_fields", ["missing_file"])

    warnings: list[str] = []
    try:
        if suffix in {".html", ".htm"}:
            raw_data = _parse_html(report_path)
        elif suffix == ".xml":
            raw_data = _parse_xml(report_path)
        elif suffix == ".csv":
            raw_data = _parse_csv(report_path)
        else:
            raw_data = _parse_json(report_path)
    except (OSError, ET.ParseError, json.JSONDecodeError, csv.Error) as exc:
        return _empty_result(report_path, "unsupported_format_or_missing_fields", [type(exc).__name__])

    result = _build_result(report_path, raw_data, warnings)
    if not result.parseable:
        return ParsedMT5Report(
            **{
                **result.to_dict(),
                "result_status": "unsupported_format_or_missing_fields",
                "warnings": [*result.warnings, "missing_known_fields"],
            }
        )
    return result
