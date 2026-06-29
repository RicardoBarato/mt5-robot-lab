"""Safe local MetaTrader 5 detection and diagnostics.

This module only detects files and writes diagnostics. It does not execute MT5,
does not launch Strategy Tester, does not connect to accounts and does not read
broker credentials.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable


COMMON_SYMBOLS = [
    "XAUUSD",
    "XAUUSD.",
    "XAUUSDm",
    "GOLD",
    "GOLDmicro",
    "US30",
    "US30.cash",
    "DJ30",
    "USTEC",
    "USTEC.cash",
    "NAS100",
    "US100",
    "EURUSD",
    "GBPUSD",
    "BTCUSD",
    "BTCUSD.",
    "BTCUSDm",
]

USER_HOME_PLACEHOLDER = "<USER_HOME>"
LOCAL_APPDATA_PLACEHOLDER = "<LOCAL_APPDATA>"
APPDATA_PLACEHOLDER = "<APPDATA>"
WINDOWS_PATH_PLACEHOLDER = "<WINDOWS_PATH_REDACTED>"
NETWORK_PATH_PLACEHOLDER = "<NETWORK_PATH_REDACTED>"
FILE_URI_PLACEHOLDER = "<FILE_URI_REDACTED>"

_WINDOWS_PATH_RE = re.compile(r"(?i)^[a-z]:[\\/]")
_WINDOWS_USERS_RE = re.compile(r"(?i)^[a-z]:[\\/]users[\\/][^\\/]+")
_UNC_PATH_RE = re.compile(r"^(\\\\|//)[^\\/]+[\\/][^\\/]+")
_PRIVATE_TEXT_PATTERNS = [
    re.compile(r"(?i)[a-z]:[\\/]users[\\/]"),
    re.compile(r"(?i)(\\\\|//)[^\\/\s]+[\\/][^\\/\s]+"),
    re.compile(r"(?i)file://"),
    re.compile(r"(?i)\bappdata\b"),
    re.compile(r"(?i)\bdocuments[\\/]"),
    re.compile(r"(?i)%userprofile%"),
    re.compile(r"(?i)%appdata%"),
    re.compile(r"(?i)%localappdata%"),
]

LOCAL_MT5_CONFIG_PATH = Path("config") / "mt5.local.json"
E_DRIVE_PROBABLE_ROOTS = [
    Path("E:/MetaTrader 5"),
    Path("E:/MT5"),
    Path("E:/Tickmill MT5"),
    Path("E:/Tickmill MetaTrader 5"),
    Path("E:/Program Files/MetaTrader 5"),
    Path("E:/MetaQuotes"),
    Path("E:/MetaQuotes/Terminal"),
]


@dataclass(frozen=True)
class MT5DetectionResult:
    terminal_path: str
    metaeditor_path: str
    terminal_found: bool
    metaeditor_found: bool
    mt5_installed: bool
    status: str
    scanned_locations: list[str]
    local_config_loaded: bool = False
    custom_terminal_path_configured: bool = False
    custom_metaeditor_path_configured: bool = False
    custom_path_errors: list[str] = field(default_factory=list)
    e_drive_detection_enabled: bool = True

    @property
    def terminal64(self) -> str | None:
        return self.terminal_path or None

    @property
    def metaeditor64(self) -> str | None:
        return self.metaeditor_path or None

    @property
    def terminal_detected(self) -> bool:
        return self.terminal_found

    @property
    def metaeditor_detected(self) -> bool:
        return self.metaeditor_found


def _path_from_env(name: str) -> Path | None:
    value = os.environ.get(name)
    if not value:
        return None
    return Path(value)


def common_mt5_roots() -> list[Path]:
    roots: list[Path] = []
    program_files = _path_from_env("ProgramFiles")
    program_files_x86 = _path_from_env("ProgramFiles(x86)")
    local_appdata = _path_from_env("LOCALAPPDATA")
    appdata = _path_from_env("APPDATA")
    userprofile = _path_from_env("USERPROFILE")

    for base in (program_files, program_files_x86):
        if base:
            roots.extend([base / "MetaTrader 5", base / "MetaQuotes" / "MetaTrader 5"])
    if local_appdata:
        roots.extend([local_appdata / "Programs" / "MetaTrader 5", local_appdata / "MetaQuotes" / "Terminal"])
    if appdata:
        roots.append(appdata / "MetaQuotes" / "Terminal")
    if userprofile:
        roots.extend(
            [
                userprofile / "AppData" / "Roaming" / "MetaQuotes" / "Terminal",
                userprofile / "AppData" / "Local" / "MetaQuotes" / "Terminal",
                userprofile / "AppData" / "Local" / "Programs" / "MetaTrader 5",
            ]
        )

    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root)
        if key not in seen:
            unique.append(root)
            seen.add(key)
    return unique


def e_drive_mt5_roots() -> list[Path]:
    return list(E_DRIVE_PROBABLE_ROOTS)


def _dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path).lower()
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return unique


def _iter_limited_candidates(root: Path, filename: str) -> Iterable[Path]:
    yield root / filename
    terminal_root = root.name.lower() == "terminal"
    if not root.exists() or not root.is_dir():
        return
    try:
        children = list(root.iterdir())[:80] if terminal_root else []
    except OSError:
        children = []
    for child in children:
        yield child / filename


def _find_file(filename: str, roots: list[Path] | None = None) -> tuple[Path | None, list[str]]:
    scan_roots = roots or common_mt5_roots()
    scanned: list[str] = []
    for root in scan_roots:
        scanned.append(_public_path(root))
        for candidate in _iter_limited_candidates(root, filename):
            try:
                if candidate.exists() and candidate.is_file():
                    return candidate, scanned
            except OSError:
                continue
    return None, scanned


def load_local_mt5_config(config_path: Path | None = None) -> dict[str, str]:
    path = config_path or LOCAL_MT5_CONFIG_PATH
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"_error": f"local_config_unreadable:{exc}"}
    if not isinstance(payload, dict):
        return {"_error": "local_config_must_be_json_object"}
    return {
        key: str(payload.get(key, "") or "")
        for key in ("terminal_path", "metaeditor_path")
        if payload.get(key)
    }


def _manual_executable(path_value: str | None, expected_name: str) -> tuple[Path | None, str | None]:
    if not path_value:
        return None, None
    try:
        return validate_mt5_executable_path(path_value, expected_name), None
    except (OSError, ValueError) as exc:
        return None, f"{expected_name}:{exc}"


def _placeholder_with_suffix(placeholder: str, suffix: str) -> str:
    suffix = suffix.replace("/", "\\")
    return placeholder + suffix if suffix.startswith("\\") else placeholder + ("\\" + suffix if suffix else "")


def redact_public_path(path: Path | str | None) -> str:
    """Return a public-safe representation of a local path."""
    if not path:
        return ""
    text = str(path)
    stripped = text.strip()
    lowered = stripped.lower()

    if lowered.startswith("file://"):
        return FILE_URI_PLACEHOLDER
    if _UNC_PATH_RE.match(stripped):
        return NETWORK_PATH_PLACEHOLDER

    env_placeholders = {
        "%LOCALAPPDATA%": LOCAL_APPDATA_PLACEHOLDER,
        "%APPDATA%": APPDATA_PLACEHOLDER,
        "%USERPROFILE%": USER_HOME_PLACEHOLDER,
    }
    for source, target in env_placeholders.items():
        if lowered.startswith(source.lower()):
            return _placeholder_with_suffix(target, stripped[len(source) :])

    replacements = [
        (os.environ.get("LOCALAPPDATA", ""), LOCAL_APPDATA_PLACEHOLDER),
        (os.environ.get("APPDATA", ""), APPDATA_PLACEHOLDER),
        (os.environ.get("USERPROFILE", ""), USER_HOME_PLACEHOLDER),
    ]
    for source, target in sorted(((s, t) for s, t in replacements if s), key=lambda item: len(item[0]), reverse=True):
        if stripped.lower().startswith(source.lower()):
            return _placeholder_with_suffix(target, stripped[len(source) :])

    if _WINDOWS_USERS_RE.match(stripped):
        match = _WINDOWS_USERS_RE.match(stripped)
        suffix = stripped[match.end() :] if match else ""
        return _placeholder_with_suffix(USER_HOME_PLACEHOLDER, suffix)
    if _WINDOWS_PATH_RE.match(stripped):
        basename = Path(stripped).name
        return _placeholder_with_suffix(WINDOWS_PATH_PLACEHOLDER, basename)
    if "appdata" in lowered:
        return WINDOWS_PATH_PLACEHOLDER
    return stripped


def _public_path(path: Path | str | None) -> str:
    return redact_public_path(path)


def is_private_path_text(text: str) -> bool:
    return any(pattern.search(text) for pattern in _PRIVATE_TEXT_PATTERNS)


def validate_mt5_executable_path(path: str | Path, expected_name: str) -> Path:
    candidate = Path(path)
    if not str(path).strip():
        raise ValueError(f"{expected_name} path is required")
    if candidate.name.lower() != expected_name.lower():
        raise ValueError(f"Expected {expected_name}, got {candidate.name or 'empty path'}")
    if candidate.suffix.lower() != ".exe":
        raise ValueError(f"{expected_name} must be a Windows .exe")
    if not candidate.exists() or not candidate.is_file():
        raise FileNotFoundError(f"{expected_name} was not found")
    return candidate


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def validate_tester_config_path(path: str | Path, allowed_roots: list[Path] | None = None) -> Path:
    candidate = Path(path)
    if not str(path).strip():
        raise ValueError("tester_config_path is required")
    if candidate.suffix.lower() in {".set", ".tst", ".ex5", ".env"}:
        raise ValueError("tester_config_path cannot be a preset, tester file, compiled EA or env file")
    if candidate.suffix.lower() not in {".ini", ".cfg"}:
        raise ValueError("tester_config_path must be a local .ini or .cfg file")
    if not candidate.exists() or not candidate.is_file():
        raise FileNotFoundError("tester_config_path was not found")

    roots = allowed_roots or [Path.cwd() / "config", Path.cwd() / "runs"]
    if not any(_is_within(candidate, root) for root in roots):
        raise ValueError("tester_config_path must stay inside approved local config or ignored run folders")
    return candidate


def find_terminal(roots: list[Path] | None = None) -> str:
    return detect_mt5(roots).terminal_path


def find_metaeditor(roots: list[Path] | None = None) -> str:
    return detect_mt5(roots).metaeditor_path


def detect_mt5(
    roots: list[Path] | None = None,
    *,
    terminal_path: str | None = None,
    metaeditor_path: str | None = None,
    config_path: Path | None = None,
) -> MT5DetectionResult:
    config = load_local_mt5_config(config_path)
    local_config_loaded = bool(config)
    custom_path_errors: list[str] = []
    if config.get("_error"):
        custom_path_errors.append(str(config["_error"]))

    configured_terminal = terminal_path or config.get("terminal_path")
    configured_metaeditor = metaeditor_path or config.get("metaeditor_path")
    terminal, terminal_error = _manual_executable(configured_terminal, "terminal64.exe")
    metaeditor, metaeditor_error = _manual_executable(configured_metaeditor, "metaeditor64.exe")
    if terminal_error:
        custom_path_errors.append(terminal_error)
    if metaeditor_error:
        custom_path_errors.append(metaeditor_error)

    scan_roots = roots if roots is not None else _dedupe_paths([*common_mt5_roots(), *e_drive_mt5_roots()])
    terminal_scanned: list[str] = []
    metaeditor_scanned: list[str] = []
    if terminal is None:
        terminal, terminal_scanned = _find_file("terminal64.exe", scan_roots)
    if metaeditor is None:
        metaeditor, metaeditor_scanned = _find_file("metaeditor64.exe", scan_roots)
    scanned = list(dict.fromkeys([*terminal_scanned, *metaeditor_scanned]))
    terminal_found = terminal is not None
    metaeditor_found = metaeditor is not None
    return MT5DetectionResult(
        terminal_path=_public_path(terminal),
        metaeditor_path=_public_path(metaeditor),
        terminal_found=terminal_found,
        metaeditor_found=metaeditor_found,
        mt5_installed=terminal_found or metaeditor_found,
        status="ready" if terminal_found and metaeditor_found else "not ready",
        scanned_locations=scanned,
        local_config_loaded=local_config_loaded,
        custom_terminal_path_configured=bool(configured_terminal),
        custom_metaeditor_path_configured=bool(configured_metaeditor),
        custom_path_errors=custom_path_errors,
        e_drive_detection_enabled=roots is None,
    )


def scan_symbols(detection: MT5DetectionResult | None = None) -> dict[str, object]:
    result = detection or detect_mt5()
    # Safe mode does not connect to MT5. It returns common broker mappings only.
    return {
        "symbol_scan_mode": "safe_mock_common_mappings",
        "mt5_connected": False,
        "mt5_account_required": True,
        "mt5_account_connected": False,
        "symbols_loaded": True,
        "history_available": False,
        "symbol_detection_method": "mock_common_broker_mappings_no_terminal_execution",
        "symbols": COMMON_SYMBOLS,
        "terminal_found": result.terminal_found,
        "metaeditor_found": result.metaeditor_found,
    }


def generate_diagnostics(
    output_dir: Path,
    roots: list[Path] | None = None,
    *,
    terminal_path: str | None = None,
    metaeditor_path: str | None = None,
    config_path: Path | None = None,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    detection = detect_mt5(roots, terminal_path=terminal_path, metaeditor_path=metaeditor_path, config_path=config_path)
    symbols = scan_symbols(detection)
    diagnostics = {
        "mt5_installed": detection.mt5_installed,
        "terminal_found": detection.terminal_found,
        "metaeditor_found": detection.metaeditor_found,
        "terminal_path": detection.terminal_path,
        "metaeditor_path": detection.metaeditor_path,
        "status": detection.status,
        "scanned_locations": detection.scanned_locations,
        "real_mt5_run": False,
        "strategy_tester_run": False,
        "backtest_real_run": False,
        "credentials_requested": False,
        "credentials_stored": False,
        "symbol_scan_mode": symbols["symbol_scan_mode"],
        "local_config_loaded": detection.local_config_loaded,
        "custom_terminal_path_configured": detection.custom_terminal_path_configured,
        "custom_metaeditor_path_configured": detection.custom_metaeditor_path_configured,
        "custom_path_errors": detection.custom_path_errors,
        "e_drive_detection_enabled": detection.e_drive_detection_enabled,
    }

    diagnostics_path = output_dir / "mt5_diagnostics.json"
    symbols_path = output_dir / "mt5_symbols.json"
    status_path = output_dir / "mt5_status.md"

    diagnostics_path.write_text(json.dumps(diagnostics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    symbols_path.write_text(json.dumps(symbols, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    status_lines = [
        "# MT5 Status",
        "",
        f"- MT5 installed: {diagnostics['mt5_installed']}",
        f"- Terminal found: {diagnostics['terminal_found']}",
        f"- Terminal path: {diagnostics['terminal_path'] or 'not found'}",
        f"- MetaEditor found: {diagnostics['metaeditor_found']}",
        f"- MetaEditor path: {diagnostics['metaeditor_path'] or 'not found'}",
        f"- Status: {diagnostics['status']}",
        f"- Symbol scan: {symbols['symbol_scan_mode']}",
        "- Real MT5 run: false",
        "- Strategy Tester run: false",
        "- Backtest real run: false",
        "",
        "No account login, broker server detail or order execution is used by this diagnostic.",
    ]
    status_path.write_text("\n".join(status_lines) + "\n", encoding="utf-8")

    return {
        "status": "OK",
        "diagnostics": diagnostics,
        "symbols": symbols,
        "files": {
            "diagnostics": str(diagnostics_path),
            "symbols": str(symbols_path),
            "status": str(status_path),
        },
    }


def build_local_mt5_environment_status(
    roots: list[Path] | None = None,
    *,
    terminal_path: str | None = None,
    metaeditor_path: str | None = None,
    config_path: Path | None = None,
) -> dict[str, object]:
    detection = detect_mt5(roots, terminal_path=terminal_path, metaeditor_path=metaeditor_path, config_path=config_path)
    symbols = scan_symbols(detection)
    ready_for_real_smoke = bool(detection.terminal_found and detection.metaeditor_found)
    return {
        "mt5_detected": detection.mt5_installed,
        "terminal_found": detection.terminal_found,
        "metaeditor_found": detection.metaeditor_found,
        "terminal_path_sanitized": detection.terminal_path,
        "metaeditor_path_sanitized": detection.metaeditor_path,
        "status": detection.status,
        "scanned_locations_sanitized": detection.scanned_locations,
        "symbol_scan_mode": symbols["symbol_scan_mode"],
        "symbol_detection_method": symbols["symbol_detection_method"],
        "symbols_available_or_mapped": symbols["symbols"],
        "operator_gate_required": True,
        "ready_for_real_smoke": ready_for_real_smoke,
        "readiness_reason": (
            "terminal64.exe_and_metaeditor64.exe_detected_operator_gate_still_required"
            if ready_for_real_smoke
            else "terminal64.exe_or_metaeditor64.exe_not_detected"
        ),
        "mt5_real_run": False,
        "backtest_real_run": False,
        "strategy_tester_run": False,
        "ea_executed": False,
        "tournament_100_run": False,
        "credentials_requested": False,
        "credentials_stored": False,
        "broker_server_stored": False,
        "paths_sanitized": True,
        "local_config_loaded": detection.local_config_loaded,
        "custom_terminal_path_configured": detection.custom_terminal_path_configured,
        "custom_metaeditor_path_configured": detection.custom_metaeditor_path_configured,
        "custom_path_errors": detection.custom_path_errors,
        "e_drive_detection_enabled": detection.e_drive_detection_enabled,
    }


def _local_environment_markdown(status: dict[str, object]) -> str:
    lines = [
        "# Local MT5 Environment Verification",
        "",
        f"- MT5 detected: {str(status['mt5_detected']).lower()}",
        f"- Terminal found: {str(status['terminal_found']).lower()}",
        f"- MetaEditor found: {str(status['metaeditor_found']).lower()}",
        f"- Terminal path sanitized: {status['terminal_path_sanitized'] or 'not found'}",
        f"- MetaEditor path sanitized: {status['metaeditor_path_sanitized'] or 'not found'}",
        f"- Symbol scan mode: {status['symbol_scan_mode']}",
        f"- Local config loaded: {str(status['local_config_loaded']).lower()}",
        f"- E-drive detection enabled: {str(status['e_drive_detection_enabled']).lower()}",
        f"- Operator gate required: {str(status['operator_gate_required']).lower()}",
        f"- Ready for real smoke: {str(status['ready_for_real_smoke']).lower()}",
        "- MT5 real run: false",
        "- Strategy Tester run: false",
        "- Backtest real run: false",
        "- EA executed: false",
        "- 100-test tournament: false",
        "- Credentials stored: false",
        "",
        "This verification only detects the local environment and common broker symbol mappings.",
        "It does not launch MT5, does not run Strategy Tester and does not store broker login details.",
    ]
    return "\n".join(lines) + "\n"


def _custom_path_report_markdown(status: dict[str, object]) -> str:
    lines = [
        "# MVP-013B2 Custom MT5 Path Detection Report",
        "",
        f"- MT5 detected: {str(status['mt5_detected']).lower()}",
        f"- Terminal found: {str(status['terminal_found']).lower()}",
        f"- MetaEditor found: {str(status['metaeditor_found']).lower()}",
        f"- Terminal path sanitized: {status['terminal_path_sanitized'] or 'not found'}",
        f"- MetaEditor path sanitized: {status['metaeditor_path_sanitized'] or 'not found'}",
        f"- Local config loaded: {str(status['local_config_loaded']).lower()}",
        f"- E-drive detection enabled: {str(status['e_drive_detection_enabled']).lower()}",
        f"- Symbol scan mode: {status['symbol_scan_mode']}",
        f"- Operator gate required: {str(status['operator_gate_required']).lower()}",
        f"- Ready for real smoke: {str(status['ready_for_real_smoke']).lower()}",
        "- MT5 real run: false",
        "- Strategy Tester run: false",
        "- Backtest real run: false",
        "- EA executed: false",
        "- Credentials stored: false",
        "",
        "This report supports custom MT5 installation paths, including E-drive candidates.",
        "It does not launch MT5, does not run Strategy Tester and does not store broker login details.",
    ]
    return "\n".join(lines) + "\n"


def write_local_mt5_environment_status(
    output_dir: Path,
    roots: list[Path] | None = None,
    *,
    terminal_path: str | None = None,
    metaeditor_path: str | None = None,
    config_path: Path | None = None,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    status = build_local_mt5_environment_status(
        roots,
        terminal_path=terminal_path,
        metaeditor_path=metaeditor_path,
        config_path=config_path,
    )
    json_path = output_dir / "local_mt5_environment_status.json"
    markdown_path = output_dir / "local_mt5_environment_status.md"
    report_path = output_dir / "MVP_013B2_CUSTOM_MT5_PATH_DETECTION_REPORT.md"
    json_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(_local_environment_markdown(status), encoding="utf-8")
    report_path.write_text(_custom_path_report_markdown(status), encoding="utf-8")
    return {
        "status": "OK",
        "environment": status,
        "files": {
            "json": str(json_path),
            "markdown": str(markdown_path),
            "custom_path_report": str(report_path),
        },
    }


def symbol_discovery_stub() -> dict[str, object]:
    return scan_symbols()
