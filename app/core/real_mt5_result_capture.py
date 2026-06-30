"""Private result capture contract for future real MT5 smoke runs.

The capture contract defines where a future one-run smoke stores local artifacts
and how the private manifest records discovered report files. It does not launch
MT5, does not scan outside its run directory and does not publish raw paths.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.core.mt5_process_control import make_mt5_close_summary
from app.core.strategy_tester_report_config import (
    build_strategy_tester_report_contract,
    expected_report_candidates,
)


SUPPORTED_REPORT_EXTENSIONS = {".html", ".htm", ".xml", ".csv", ".json"}
SUPPORTED_LOG_EXTENSIONS = {".txt", ".log", ".journal"}
PRIVATE_CAPTURE_ROOT = Path("reports") / "private" / "real_mt5_smoke"
LOCAL_MANIFEST_NAME = "run_manifest.local.json"
INTERNAL_ARTIFACT_NAMES = {
    LOCAL_MANIFEST_NAME,
    "environment_sanitized.json",
    "operator_gate_manifest.json",
    "execution_manifest.json",
    "run_summary_sanitized.json",
}


@dataclass(frozen=True)
class ResultCaptureManifest:
    run_id: str
    started_at: str
    ended_at: str | None
    return_code: int | None
    requested_symbol: str
    requested_timeframe: str
    expected_report_paths: list[str]
    observed_report_files: list[str]
    observed_log_files: list[str]
    capture_status: str
    parse_status: str
    report_export_configured: bool = False
    report_base: str = ""
    replace_report: bool = True
    shutdown_terminal: bool = True
    report_required: bool = True
    parse_required: bool = True
    private_artifacts_only: bool = True
    public_summary_sanitized: bool = True
    report_capture_attempted: bool = False
    report_capture_status: str = "initialized"
    parser_attempted: bool = False
    mt5_close_policy: str = "not_applicable"
    mt5_close_attempted: bool = False
    mt5_closed_after_run: bool = False
    mt5_close_method: str = "not_applicable"
    mt5_close_error: str = ""
    mt5_process_owned_by_app: bool = False
    mt5_external_process_detected: bool = False
    manual_close_required: bool = False
    failure_stage: str = "not_attempted"
    exit_code_category: str = "not_recorded"
    preflight_status: str = "not_evaluated"
    ready_for_real_retry: bool = False
    preflight_blocking_issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ResultCaptureContext:
    run_id: str
    run_dir: Path
    manifest_path: Path
    expected_report_paths: list[Path] = field(default_factory=list)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def make_run_id(prefix: str = "real_smoke") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{stamp}_{uuid4().hex[:8]}"


def _assert_inside(child: Path, parent: Path) -> None:
    child.resolve().relative_to(parent.resolve())


def create_capture_context(
    project_root: Path,
    *,
    run_id: str | None = None,
    requested_symbol: str = "XAUUSD",
    requested_timeframe: str = "M5",
) -> ResultCaptureContext:
    """Create a private run folder and local manifest path for a future smoke."""

    clean_run_id = run_id or make_run_id()
    if any(part in clean_run_id for part in ("..", "\\", "/")):
        raise ValueError("run_id must be a simple path segment")

    private_root = project_root / PRIVATE_CAPTURE_ROOT
    run_dir = private_root / clean_run_id
    _assert_inside(run_dir, private_root)
    run_dir.mkdir(parents=True, exist_ok=True)

    report_contract = build_strategy_tester_report_contract(clean_run_id)
    expected_report_paths = [project_root / Path(path) for path in expected_report_candidates(clean_run_id)]
    manifest = ResultCaptureManifest(
        run_id=clean_run_id,
        started_at=utc_now(),
        ended_at=None,
        return_code=None,
        requested_symbol=requested_symbol,
        requested_timeframe=requested_timeframe,
        expected_report_paths=[path.name for path in expected_report_paths],
        observed_report_files=[],
        observed_log_files=[],
        capture_status="initialized",
        parse_status="not_parsed",
        report_export_configured=bool(report_contract["report_export_configured"]),
        report_base=str(report_contract["report_base"]),
        replace_report=bool(report_contract["replace_report"]),
        shutdown_terminal=bool(report_contract["shutdown_terminal"]),
        report_required=bool(report_contract["report_required"]),
        parse_required=bool(report_contract["parse_required"]),
        private_artifacts_only=bool(report_contract["private_artifacts_only"]),
        public_summary_sanitized=bool(report_contract["public_summary_sanitized"]),
        report_capture_attempted=False,
        report_capture_status="initialized",
        parser_attempted=False,
        **make_mt5_close_summary(None),
    )
    manifest_path = run_dir / LOCAL_MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ResultCaptureContext(
        run_id=clean_run_id,
        run_dir=run_dir,
        manifest_path=manifest_path,
        expected_report_paths=expected_report_paths,
    )


def discover_capture_artifacts(run_dir: Path) -> dict[str, list[str]]:
    """List report and log artifact names in a single private run folder only."""

    if not run_dir.exists() or not run_dir.is_dir():
        return {"observed_report_files": [], "observed_log_files": []}
    report_files: list[str] = []
    log_files: list[str] = []
    for path in sorted(run_dir.iterdir()):
        if not path.is_file():
            continue
        if path.name in INTERNAL_ARTIFACT_NAMES:
            continue
        suffix = path.suffix.lower()
        if suffix in SUPPORTED_REPORT_EXTENSIONS:
            report_files.append(path.name)
        elif suffix in SUPPORTED_LOG_EXTENSIONS:
            log_files.append(path.name)
    return {"observed_report_files": report_files, "observed_log_files": log_files}


def write_capture_manifest(
    context: ResultCaptureContext,
    *,
    return_code: int | None,
    capture_status: str,
    parse_status: str,
    requested_symbol: str = "XAUUSD",
    requested_timeframe: str = "M5",
    close_summary: dict[str, object] | None = None,
    report_contract: dict[str, object] | None = None,
    preflight_summary: dict[str, object] | None = None,
) -> ResultCaptureManifest:
    artifacts = discover_capture_artifacts(context.run_dir)
    contract = report_contract or build_strategy_tester_report_contract(context.run_id)
    parser_attempted = parse_status not in {"not_parsed", "pending_report_discovery", "no_report_found"}
    manifest = ResultCaptureManifest(
        run_id=context.run_id,
        started_at=utc_now(),
        ended_at=utc_now(),
        return_code=return_code,
        requested_symbol=requested_symbol,
        requested_timeframe=requested_timeframe,
        expected_report_paths=[path.name for path in context.expected_report_paths],
        observed_report_files=artifacts["observed_report_files"],
        observed_log_files=artifacts["observed_log_files"],
        capture_status=capture_status,
        parse_status=parse_status,
        report_export_configured=bool(contract["report_export_configured"]),
        report_base=str(contract["report_base"]),
        replace_report=bool(contract["replace_report"]),
        shutdown_terminal=bool(contract["shutdown_terminal"]),
        report_required=bool(contract["report_required"]),
        parse_required=bool(contract["parse_required"]),
        private_artifacts_only=bool(contract["private_artifacts_only"]),
        public_summary_sanitized=bool(contract["public_summary_sanitized"]),
        report_capture_attempted=capture_status not in {"initialized", "not_attempted"},
        report_capture_status=capture_status,
        parser_attempted=parser_attempted,
        failure_stage=str(preflight_summary.get("failure_stage", "not_attempted")) if preflight_summary else "not_attempted",
        exit_code_category=str(preflight_summary.get("exit_code_category", "not_recorded"))
        if preflight_summary
        else "not_recorded",
        preflight_status=str(preflight_summary.get("status", "not_evaluated")) if preflight_summary else "not_evaluated",
        ready_for_real_retry=bool(preflight_summary.get("ready_for_real_retry", False)) if preflight_summary else False,
        preflight_blocking_issues=list(preflight_summary.get("blocking_issues", [])) if preflight_summary else [],
        **make_mt5_close_summary(close_summary),
    )
    context.manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest
