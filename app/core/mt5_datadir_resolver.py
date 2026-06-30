"""Resolve the local MT5 terminal DataDir without launching MT5.

This module reads local configuration and MetaQuotes `origin.txt` metadata only.
It does not execute terminal64.exe, MetaEditor, Strategy Tester, or an EA.
Raw paths are returned for internal checks; public summaries must use the
sanitized fields.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import os
from pathlib import Path

from app.core.mt5_detection import (
    LOCAL_MT5_CONFIG_PATH,
    load_local_mt5_config,
    redact_public_path,
    resolve_mt5_execution_paths,
)


@dataclass(frozen=True)
class MT5DataDirResolution:
    terminal_data_dir_found: bool
    terminal_data_dir: str
    terminal_data_dir_sanitized: str
    datadir_source: str
    terminal_data_dir_structure_valid: bool
    mql5_dir_found: bool
    experts_dir_found: bool
    tester_profiles_dir_found: bool
    terminal_path_sanitized: str
    origin_txt_found: bool
    origin_txt_matched_terminal: bool
    blocking_issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _expand_config_path(value: str) -> Path:
    expanded = os.path.expandvars(str(value or "").strip())
    return Path(expanded)


def _same_or_parent(path_text: str, terminal: Path | None) -> bool:
    if not terminal or not path_text.strip():
        return False
    candidate = _expand_config_path(path_text)
    texts = {
        str(candidate).replace("/", "\\").rstrip("\\").lower(),
        str(candidate / "terminal64.exe").replace("/", "\\").rstrip("\\").lower(),
    }
    terminal_text = str(terminal).replace("/", "\\").rstrip("\\").lower()
    terminal_parent = str(terminal.parent).replace("/", "\\").rstrip("\\").lower()
    return terminal_text in texts or terminal_parent in texts


def _validate_datadir(path: Path) -> dict[str, object]:
    mql5 = path / "MQL5"
    experts = mql5 / "Experts"
    tester_profiles = mql5 / "Profiles" / "Tester"
    mql5_found = mql5.exists() and mql5.is_dir()
    experts_found = experts.exists() and experts.is_dir()
    return {
        "mql5_dir_found": mql5_found,
        "experts_dir_found": experts_found,
        "tester_profiles_dir_found": tester_profiles.exists() and tester_profiles.is_dir(),
        "terminal_data_dir_structure_valid": bool(mql5_found and experts_found),
    }


def _appdata_terminal_root() -> Path | None:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    return Path(appdata) / "MetaQuotes" / "Terminal"


def _iter_origin_candidates() -> list[Path]:
    root = _appdata_terminal_root()
    if not root or not root.exists() or not root.is_dir():
        return []
    try:
        children = sorted(root.iterdir(), key=lambda item: item.name.lower())
    except OSError:
        return []
    return [child / "origin.txt" for child in children[:200]]


def _read_origin(origin_path: Path) -> str:
    try:
        return origin_path.read_text(encoding="utf-16").strip()
    except UnicodeError:
        try:
            return origin_path.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError:
            return ""
    except OSError:
        return ""


def _result(
    *,
    terminal_data_dir: Path | None,
    datadir_source: str,
    terminal_path: Path | None = None,
    origin_txt_found: bool = False,
    origin_txt_matched_terminal: bool = False,
    warnings: list[str] | None = None,
) -> dict[str, object]:
    issues: list[str] = []
    if terminal_data_dir is None:
        issues.append("terminal_data_dir_missing")
        validation = {
            "mql5_dir_found": False,
            "experts_dir_found": False,
            "tester_profiles_dir_found": False,
            "terminal_data_dir_structure_valid": False,
        }
    else:
        validation = _validate_datadir(terminal_data_dir)
        if not validation["terminal_data_dir_structure_valid"]:
            issues.append("terminal_data_dir_structure_invalid")
    payload = MT5DataDirResolution(
        terminal_data_dir_found=bool(terminal_data_dir is not None and validation["terminal_data_dir_structure_valid"]),
        terminal_data_dir=str(terminal_data_dir or ""),
        terminal_data_dir_sanitized=redact_public_path(terminal_data_dir) if terminal_data_dir else "",
        datadir_source=datadir_source,
        terminal_data_dir_structure_valid=bool(validation["terminal_data_dir_structure_valid"]),
        mql5_dir_found=bool(validation["mql5_dir_found"]),
        experts_dir_found=bool(validation["experts_dir_found"]),
        tester_profiles_dir_found=bool(validation["tester_profiles_dir_found"]),
        terminal_path_sanitized=redact_public_path(terminal_path) if terminal_path else "",
        origin_txt_found=origin_txt_found,
        origin_txt_matched_terminal=origin_txt_matched_terminal,
        blocking_issues=issues,
        warnings=warnings or [],
    )
    return payload.to_dict()


def resolve_terminal_datadir(
    project_root: Path,
    *,
    terminal_path: str | Path | None = None,
    config_path: Path | None = None,
) -> dict[str, object]:
    """Resolve a terminal DataDir from ignored local config or origin.txt."""

    config_file = config_path or project_root / LOCAL_MT5_CONFIG_PATH
    config = load_local_mt5_config(config_file)
    config_data_dir = str(config.get("terminal_data_dir", "") or "")
    raw_terminal, _raw_metaeditor = resolve_mt5_execution_paths(
        terminal_path=str(terminal_path) if terminal_path else None,
        config_path=config_file,
    )
    if config_data_dir:
        data_dir = _expand_config_path(config_data_dir)
        return _result(
            terminal_data_dir=data_dir,
            datadir_source="config_mt5_local_json",
            terminal_path=raw_terminal,
            warnings=[] if data_dir.exists() else ["configured_terminal_data_dir_not_found"],
        )

    origin_candidates = _iter_origin_candidates()
    for origin in origin_candidates:
        if not origin.exists() or not origin.is_file():
            continue
        origin_text = _read_origin(origin)
        matched = _same_or_parent(origin_text, raw_terminal)
        if not matched:
            continue
        data_dir = origin.parent
        return _result(
            terminal_data_dir=data_dir,
            datadir_source="appdata_origin_txt",
            terminal_path=raw_terminal,
            origin_txt_found=True,
            origin_txt_matched_terminal=True,
        )

    return _result(
        terminal_data_dir=None,
        datadir_source="not_found",
        terminal_path=raw_terminal,
        origin_txt_found=bool(origin_candidates),
        origin_txt_matched_terminal=False,
    )


def public_datadir_resolution_summary(resolution: dict[str, object]) -> dict[str, object]:
    return {
        "terminal_data_dir_found": bool(resolution.get("terminal_data_dir_found")),
        "terminal_data_dir_sanitized": str(resolution.get("terminal_data_dir_sanitized", "")),
        "datadir_source": str(resolution.get("datadir_source", "")),
        "terminal_data_dir_structure_valid": bool(resolution.get("terminal_data_dir_structure_valid")),
        "mql5_dir_found": bool(resolution.get("mql5_dir_found")),
        "experts_dir_found": bool(resolution.get("experts_dir_found")),
        "tester_profiles_dir_found": bool(resolution.get("tester_profiles_dir_found")),
        "terminal_path_sanitized": str(resolution.get("terminal_path_sanitized", "")),
        "origin_txt_found": bool(resolution.get("origin_txt_found")),
        "origin_txt_matched_terminal": bool(resolution.get("origin_txt_matched_terminal")),
        "blocking_issues": list(resolution.get("blocking_issues", [])),
        "warnings": list(resolution.get("warnings", [])),
    }
