"""Asset-to-broker-symbol mapping helpers."""

from __future__ import annotations


SYMBOL_CANDIDATES = {
    "gold_xau": ["XAUUSD", "XAUUSD.", "XAUUSDm", "GOLD", "GOLDmicro"],
    "nasdaq_ustec": ["USTEC", "USTEC.cash", "NAS100", "US100", "US100.cash"],
    "dow_us30": ["US30", "US30.cash", "DJ30", "WallStreet30"],
    "bitcoin": ["BTCUSD", "BTCUSD.", "BTCUSDm", "BTCUSD.cash"],
}

TIMEFRAME_MINUTES = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}


def candidates_for_asset(asset_key: str) -> list[str]:
    return list(SYMBOL_CANDIDATES.get(asset_key, []))


def suggest_symbol(requested_symbol: str, available_symbols: list[str] | None = None) -> str:
    available = set(available_symbols or [])
    probe = requested_symbol.upper()
    for symbols in SYMBOL_CANDIDATES.values():
        if requested_symbol in symbols:
            for symbol in symbols:
                if symbol in available:
                    return symbol
            return symbols[0]
    for asset_key, symbols in SYMBOL_CANDIDATES.items():
        if any(part in probe for part in asset_key.upper().split("_")):
            for symbol in symbols:
                if symbol in available:
                    return symbol
            return symbols[0]
    return requested_symbol


def timeframe_minutes(timeframe: str) -> int:
    if timeframe not in TIMEFRAME_MINUTES:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    return TIMEFRAME_MINUTES[timeframe]
