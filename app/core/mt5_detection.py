"""Safe local MT5 detection stubs.

The functions here do not run MT5 and do not scan the whole disk aggressively.
They check a short list of common locations and return status metadata.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MT5DetectionResult:
    terminal64: str | None
    metaeditor64: str | None
    terminal_detected: bool
    metaeditor_detected: bool
    scanned_locations: list[str]


def common_mt5_roots() -> list[Path]:
    roots = [
        Path(os.environ.get("ProgramFiles", "")) / "MetaTrader 5",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "MetaTrader 5",
    ]
    appdata = os.environ.get("APPDATA")
    if appdata:
        roots.append(Path(appdata) / "MetaQuotes" / "Terminal")
    return [root for root in roots if str(root)]


def _find_file(root: Path, name: str) -> Path | None:
    direct = root / name
    if direct.exists():
        return direct
    if root.name == "Terminal" and root.exists():
        for child in list(root.iterdir())[:50]:
            candidate = child / name
            if candidate.exists():
                return candidate
    return None


def detect_mt5() -> MT5DetectionResult:
    scanned: list[str] = []
    terminal: Path | None = None
    metaeditor: Path | None = None
    for root in common_mt5_roots():
        scanned.append(str(root))
        if terminal is None:
            terminal = _find_file(root, "terminal64.exe")
        if metaeditor is None:
            metaeditor = _find_file(root, "metaeditor64.exe")
    return MT5DetectionResult(
        terminal64=str(terminal) if terminal else None,
        metaeditor64=str(metaeditor) if metaeditor else None,
        terminal_detected=terminal is not None,
        metaeditor_detected=metaeditor is not None,
        scanned_locations=scanned,
    )


def symbol_discovery_stub() -> dict[str, object]:
    return {
        "mt5_connected": False,
        "mt5_account_required": True,
        "mt5_account_connected": False,
        "symbols_loaded": False,
        "history_available": False,
        "symbol_detection_method": "not_checked_stub",
    }
