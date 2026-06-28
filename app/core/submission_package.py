"""Local public-safe submission package generation for future leaderboards."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACKAGE_VERSION = "1.0"
APP_VERSION = "mvp-009"

REQUIRED_FILES = {
    "submission_manifest.json",
    "champion_dna.json",
    "tournament_summary.json",
    "risk_profile.json",
    "config_public_summary.json",
    "file_hashes.json",
    "validation_report.json",
    "public_summary.md",
}

REQUIRED_MANIFEST_FIELDS = {
    "submission_id",
    "created_at",
    "product_name",
    "app_version",
    "package_version",
    "lab_id",
    "lab_name",
    "requested_symbol",
    "broker_symbol",
    "timeframe",
    "timeframe_minutes",
    "backtest_years",
    "initial_balance_usd",
    "risk_profile",
    "risk_mode",
    "max_drawdown_tolerated_pct",
    "ranking_profile",
    "champion_id",
    "candidate_id",
    "net_profit_usd",
    "max_drawdown_pct",
    "profit_factor",
    "total_trades",
    "win_rate",
    "mt5_real_run",
    "backtest_real_run",
    "tournament_100_run",
    "codex_used",
    "codex_authorized",
    "local_only",
    "upload_ready",
    "validation_status",
    "file_hashes",
    "notes",
}

FORBIDDEN_FILE_PATTERNS = [".env", ".set", ".ex5"]
FORBIDDEN_TEXT = [
    "password",
    "token",
    "secret",
    "account_number",
    "broker_password",
    ".env",
    ".set",
    ".ex5",
]
PRIVATE_PATH_PATTERN = re.compile(r"[A-Za-z]:\\(?!mt5-robot-lab\\reports\\public\\submission_package_sample)", re.IGNORECASE)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _as_dict(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return dict(value)
    raise TypeError("expected dataclass or dict")


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_json(data: Any) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_submission_manifest(package_dir: Path, files: dict[str, Path]) -> dict[str, Any]:
    champion = json.loads(files["champion_dna.json"].read_text(encoding="utf-8"))
    tournament = json.loads(files["tournament_summary.json"].read_text(encoding="utf-8"))
    risk_profile = json.loads(files["risk_profile.json"].read_text(encoding="utf-8"))
    config = json.loads(files["config_public_summary.json"].read_text(encoding="utf-8"))
    file_hashes = {name: hash_file(path) for name, path in sorted(files.items())}
    submission_source = {
        "champion_id": champion.get("champion_id", ""),
        "candidate_id": champion.get("candidate_id", ""),
        "candidate_hash": champion.get("candidate_hash", ""),
        "package_dir": package_dir.name,
    }
    return {
        "submission_id": "submission_" + hash_json(submission_source)[:16],
        "created_at": _utc_now(),
        "product_name": "MT5 Robot Lab",
        "app_version": APP_VERSION,
        "package_version": PACKAGE_VERSION,
        "lab_id": champion.get("lab_id", config.get("lab_id", "ea-xau")),
        "lab_name": champion.get("lab_name", config.get("lab_name", "XAU Robot Lab")),
        "requested_symbol": champion.get("requested_symbol", config.get("requested_symbol", "XAUUSD")),
        "broker_symbol": champion.get("broker_symbol", config.get("broker_symbol", "XAUUSD")),
        "timeframe": champion.get("timeframe", config.get("timeframe", "M5")),
        "timeframe_minutes": champion.get("timeframe_minutes", config.get("timeframe_minutes", 5)),
        "backtest_years": champion.get("backtest_years", config.get("backtest_years", 0.0)),
        "initial_balance_usd": champion.get("initial_balance_usd", config.get("initial_balance_usd", 10000.0)),
        "risk_profile": champion.get("risk_profile", risk_profile.get("risk_profile", "wild")),
        "risk_mode": champion.get("risk_mode", risk_profile.get("risk_mode", "wild")),
        "max_drawdown_tolerated_pct": champion.get(
            "max_drawdown_tolerated_pct",
            risk_profile.get("max_drawdown_tolerated_pct", 100.0),
        ),
        "ranking_profile": champion.get("ranking_profile", risk_profile.get("ranking_profile", "wild_profit")),
        "champion_id": champion.get("champion_id", ""),
        "candidate_id": champion.get("candidate_id", ""),
        "net_profit_usd": champion.get("net_profit_usd", 0.0),
        "max_drawdown_pct": champion.get("max_drawdown_pct", 0.0),
        "profit_factor": champion.get("profit_factor", 0.0),
        "total_trades": champion.get("total_trades", 0),
        "win_rate": champion.get("win_rate", 0.0),
        "mt5_real_run": False,
        "backtest_real_run": False,
        "tournament_100_run": bool(tournament.get("tournament_100_run", False)),
        "codex_used": bool(champion.get("codex_used", False)),
        "codex_authorized": bool(champion.get("codex_authorized", False)),
        "local_only": True,
        "upload_ready": False,
        "validation_status": "sample_not_real_backtest",
        "file_hashes": file_hashes,
        "notes": "Local public-safe sample package. Not uploaded and not a real backtest result.",
    }


def make_public_submission_summary(manifest: dict[str, Any]) -> str:
    lines = [
        "# Submission Package v1 Public Summary",
        "",
        f"- Submission ID: {manifest['submission_id']}",
        f"- Product: {manifest['product_name']} {manifest['app_version']}",
        f"- Champion: {manifest['champion_id']}",
        f"- Candidate: {manifest['candidate_id']}",
        f"- Lab: {manifest['lab_name']} ({manifest['lab_id']})",
        f"- Symbol/timeframe: {manifest['broker_symbol']} {manifest['timeframe']}",
        f"- Risk mode: {manifest['risk_mode']}",
        f"- Net profit USD: {manifest['net_profit_usd']}",
        f"- Max drawdown pct: {manifest['max_drawdown_pct']}",
        f"- Validation: {manifest['validation_status']}",
        "- Local only: true",
        "- Upload ready: false",
        "",
        "This package is a local public-safe sample for future ranking design. It is not uploaded and it is not a live trading recommendation.",
    ]
    return "\n".join(lines) + "\n"


def scan_submission_for_private_artifacts(package_dir: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in package_dir.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(package_dir).as_posix()
        lower_name = path.name.lower()
        lower_rel = rel.lower()
        if any(pattern in lower_name for pattern in FORBIDDEN_FILE_PATTERNS):
            findings.append({"file": rel, "reason": "forbidden_file_pattern"})
            continue
        if lower_rel.startswith("reports/private") or lower_rel.startswith("runs/"):
            findings.append({"file": rel, "reason": "private_or_run_path"})
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            findings.append({"file": rel, "reason": "unreadable_file"})
            continue
        lowered = text.lower()
        for term in FORBIDDEN_TEXT:
            if term in lowered:
                findings.append({"file": rel, "reason": "sensitive_string"})
                break
        if PRIVATE_PATH_PATTERN.search(text):
            findings.append({"file": rel, "reason": "private_local_path"})
    return findings


def load_submission_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_submission_package(package_dir: Path) -> dict[str, Any]:
    missing = sorted(name for name in REQUIRED_FILES if not (package_dir / name).exists())
    json_files = [
        "submission_manifest.json",
        "champion_dna.json",
        "tournament_summary.json",
        "risk_profile.json",
        "config_public_summary.json",
        "file_hashes.json",
        "validation_report.json",
    ]
    parsed: dict[str, Any] = {}
    parse_errors: list[str] = []
    for name in json_files:
        path = package_dir / name
        if not path.exists():
            continue
        try:
            parsed[name] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            parse_errors.append(f"{name}: {exc}")

    manifest = parsed.get("submission_manifest.json", {})
    missing_manifest_fields = sorted(REQUIRED_MANIFEST_FIELDS - set(manifest))
    hash_mismatches: list[str] = []
    for name, expected_hash in manifest.get("file_hashes", {}).items():
        path = package_dir / name
        if not path.exists():
            hash_mismatches.append(name)
            continue
        if hash_file(path) != expected_hash:
            hash_mismatches.append(name)

    private_findings = scan_submission_for_private_artifacts(package_dir)
    passed = not missing and not parse_errors and not missing_manifest_fields and not hash_mismatches and not private_findings
    return {
        "validation_status": "pass" if passed else "fail",
        "required_files_present": not missing,
        "missing_files": missing,
        "json_parse_errors": parse_errors,
        "manifest_fields_present": not missing_manifest_fields,
        "missing_manifest_fields": missing_manifest_fields,
        "hashes_valid": not hash_mismatches,
        "hash_mismatches": hash_mismatches,
        "private_artifact_scan_passed": not private_findings,
        "private_artifact_findings": private_findings,
        "mt5_real_run": False,
        "backtest_real_run": False,
        "online_upload": False,
    }


def create_submission_package(
    champion_dna: Any,
    tournament_summary: dict[str, Any],
    config: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    package_dir = Path(output_dir)
    package_dir.mkdir(parents=True, exist_ok=True)
    champion = _as_dict(champion_dna)
    tournament = {
        **tournament_summary,
        "mt5_real_run": False,
        "backtest_real_run": False,
        "tournament_100_run": False,
    }
    risk_profile = {
        "risk_profile": champion.get("risk_profile", "wild"),
        "risk_mode": champion.get("risk_mode", "wild"),
        "max_drawdown_tolerated_pct": champion.get("max_drawdown_tolerated_pct", 100.0),
        "ranking_profile": champion.get("ranking_profile", "wild_profit"),
        "ranking_reason": champion.get("ranking_reason", ""),
        "risk_flags": champion.get("risk_flags", []),
    }
    public_config = {
        "product_name": "MT5 Robot Lab",
        "lab_id": champion.get("lab_id", config.get("lab_id", "ea-xau")),
        "lab_name": champion.get("lab_name", config.get("lab_name", "XAU Robot Lab")),
        "requested_symbol": champion.get("requested_symbol", config.get("requested_symbol", "XAUUSD")),
        "broker_symbol": champion.get("broker_symbol", config.get("broker_symbol", "XAUUSD")),
        "timeframe": champion.get("timeframe", config.get("timeframe", "M5")),
        "timeframe_minutes": champion.get("timeframe_minutes", config.get("timeframe_minutes", 5)),
        "backtest_years": champion.get("backtest_years", config.get("backtest_years", 0.0)),
        "initial_balance_usd": champion.get("initial_balance_usd", config.get("initial_balance_usd", 10000.0)),
        "local_only": True,
        "upload_ready": False,
    }

    files = {
        "champion_dna.json": package_dir / "champion_dna.json",
        "tournament_summary.json": package_dir / "tournament_summary.json",
        "risk_profile.json": package_dir / "risk_profile.json",
        "config_public_summary.json": package_dir / "config_public_summary.json",
    }
    _write_json(files["champion_dna.json"], champion)
    _write_json(files["tournament_summary.json"], tournament)
    _write_json(files["risk_profile.json"], risk_profile)
    _write_json(files["config_public_summary.json"], public_config)

    manifest = build_submission_manifest(package_dir, files)
    _write_json(package_dir / "submission_manifest.json", manifest)
    _write_json(package_dir / "file_hashes.json", manifest["file_hashes"])
    (package_dir / "public_summary.md").write_text(make_public_submission_summary(manifest), encoding="utf-8")
    _write_json(package_dir / "validation_report.json", {"validation_status": "pending"})
    validation = validate_submission_package(package_dir)
    _write_json(package_dir / "validation_report.json", validation)

    return {
        "package_dir": str(package_dir),
        "manifest": manifest,
        "validation": validation,
        "files": sorted(REQUIRED_FILES),
    }
