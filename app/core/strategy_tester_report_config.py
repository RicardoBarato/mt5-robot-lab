"""Strategy Tester report export contract for future real MT5 smokes.

This module prepares the report-export paths and tester.ini lines that a future
gated run should use. It does not launch MT5, does not create a real tester.ini
with machine-local absolute paths and does not publish raw reports.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.core.mt5_detection import redact_public_path


DEFAULT_PRIVATE_OUTPUT_ROOT = Path("reports") / "private" / "real_mt5_smoke"
SUPPORTED_REPORT_FORMATS = {"html", "htm", "xml", "csv", "json"}


@dataclass(frozen=True)
class ReportExportConfig:
    report_export_enabled: bool = True
    report_formats: tuple[str, ...] = ("html", "xml")
    private_output_root: str = "reports/private/real_mt5_smoke"
    replace_report: bool = True
    shutdown_terminal: bool = True
    public_summary_enabled: bool = True
    commit_raw_reports: bool = False


@dataclass(frozen=True)
class ReportOutputPaths:
    run_id: str
    private_run_dir: str
    private_mt5_staging_dir: str
    report_base: str
    expected_report_html: str
    expected_report_xml: str
    expected_report_csv: str
    expected_report_htm: str
    expected_report_json: str
    expected_log_dir: str


def _safe_run_id(run_id: str) -> str:
    clean = str(run_id).strip()
    if not clean or any(part in clean for part in ("..", "\\", "/", ":")):
        raise ValueError("run_id must be a simple path segment")
    return clean


def _as_config(config: ReportExportConfig | dict[str, Any] | None) -> ReportExportConfig:
    if config is None:
        return default_report_export_config()
    if isinstance(config, ReportExportConfig):
        return config
    formats = config.get("report_formats", ("html", "xml"))
    return ReportExportConfig(
        report_export_enabled=bool(config.get("report_export_enabled", True)),
        report_formats=tuple(str(item).lower() for item in formats),
        private_output_root=str(config.get("private_output_root", "reports/private/real_mt5_smoke")),
        replace_report=bool(config.get("replace_report", True)),
        shutdown_terminal=bool(config.get("shutdown_terminal", True)),
        public_summary_enabled=bool(config.get("public_summary_enabled", True)),
        commit_raw_reports=bool(config.get("commit_raw_reports", False)),
    )


def default_report_export_config() -> ReportExportConfig:
    return ReportExportConfig()


def build_report_output_paths(run_id: str) -> ReportOutputPaths:
    clean_run_id = _safe_run_id(run_id)
    private_run_dir = DEFAULT_PRIVATE_OUTPUT_ROOT / clean_run_id
    report_base = private_run_dir / "strategy_tester_report"
    return ReportOutputPaths(
        run_id=clean_run_id,
        private_run_dir=str(private_run_dir),
        private_mt5_staging_dir=str(private_run_dir / "mt5_staging"),
        report_base=str(report_base),
        expected_report_html=str(report_base.with_suffix(".html")),
        expected_report_xml=str(report_base.with_suffix(".xml")),
        expected_report_csv=str(report_base.with_suffix(".csv")),
        expected_report_htm=str(report_base.with_suffix(".htm")),
        expected_report_json=str(report_base.with_suffix(".json")),
        expected_log_dir=str(private_run_dir / "logs"),
    )


def validate_report_export_config(config: ReportExportConfig | dict[str, Any] | None) -> ReportExportConfig:
    parsed = _as_config(config)
    private_root = parsed.private_output_root.replace("\\", "/").strip("/")
    if not parsed.report_export_enabled:
        raise ValueError("report_export_enabled must be true")
    if private_root.startswith("reports/public") or "reports/public" in private_root:
        raise ValueError("raw Strategy Tester reports must not target reports/public")
    if not private_root.startswith("reports/private"):
        raise ValueError("private_output_root must stay under reports/private")
    if parsed.commit_raw_reports:
        raise ValueError("commit_raw_reports must be false")
    if not parsed.replace_report:
        raise ValueError("replace_report must be true")
    if not parsed.shutdown_terminal:
        raise ValueError("shutdown_terminal must be true")
    unknown_formats = sorted(set(parsed.report_formats) - SUPPORTED_REPORT_FORMATS)
    if unknown_formats:
        raise ValueError(f"unsupported report formats: {unknown_formats}")
    return parsed


def expected_report_candidates(run_id: str) -> list[str]:
    paths = build_report_output_paths(run_id)
    return [
        paths.expected_report_html,
        paths.expected_report_htm,
        paths.expected_report_xml,
        paths.expected_report_csv,
        paths.expected_report_json,
    ]


def build_strategy_tester_report_contract(
    run_id: str,
    config: ReportExportConfig | dict[str, Any] | None = None,
) -> dict[str, object]:
    parsed = validate_report_export_config(config)
    paths = build_report_output_paths(run_id)
    return {
        **asdict(paths),
        "report_export_configured": True,
        "report_required": True,
        "parse_required": True,
        "private_artifacts_only": True,
        "public_summary_sanitized": True,
        "replace_report": parsed.replace_report,
        "shutdown_terminal": parsed.shutdown_terminal,
        "report_formats": list(parsed.report_formats),
        "expected_report_paths": expected_report_candidates(paths.run_id),
    }


def build_tester_ini_report_lines(report_contract: dict[str, object]) -> list[str]:
    report_base = str(report_contract["report_base"])
    replace_report = "1" if bool(report_contract.get("replace_report", True)) else "0"
    shutdown_terminal = "1" if bool(report_contract.get("shutdown_terminal", True)) else "0"
    return [
        f"Report={report_base}",
        f"ReplaceReport={replace_report}",
        f"ShutdownTerminal={shutdown_terminal}",
    ]


def sanitize_report_export_summary(summary: dict[str, Any]) -> dict[str, object]:
    sanitized: dict[str, object] = {}
    for key, value in summary.items():
        if isinstance(value, str):
            sanitized[key] = redact_public_path(value)
        elif isinstance(value, list):
            sanitized[key] = [redact_public_path(item) if isinstance(item, str) else item for item in value]
        elif isinstance(value, dict):
            sanitized[key] = sanitize_report_export_summary(value)
        else:
            sanitized[key] = value
    return sanitized


def make_report_export_summary(config: ReportExportConfig | dict[str, Any] | None = None) -> dict[str, object]:
    parsed = validate_report_export_config(config)
    run_id = "report_export_contract_preview"
    contract = build_strategy_tester_report_contract(run_id, parsed)
    summary = {
        "report_export_enabled": parsed.report_export_enabled,
        "report_formats": list(parsed.report_formats),
        "private_output_root": parsed.private_output_root,
        "replace_report": parsed.replace_report,
        "shutdown_terminal": parsed.shutdown_terminal,
        "public_summary_enabled": parsed.public_summary_enabled,
        "commit_raw_reports": parsed.commit_raw_reports,
        "report_export_configured": contract["report_export_configured"],
        "report_base": contract["report_base"],
        "expected_report_paths": contract["expected_report_paths"],
        "private_artifacts_only": contract["private_artifacts_only"],
        "public_summary_sanitized": contract["public_summary_sanitized"],
    }
    return sanitize_report_export_summary(summary)
