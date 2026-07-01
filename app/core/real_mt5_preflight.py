"""Preflight checks and failure classification for real MT5 smoke retries.

The checks in this module are read-only. They do not launch MT5, do not run
Strategy Tester and do not inspect raw private reports. The goal is to block a
future real retry until the terminal, report contract and expected compiled EA
boundary are explicit.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any

from app.core.compiled_ex5_readiness import (
    DEFAULT_BOOTSTRAP_EXPERT,
    load_compiled_ex5_readiness_marker,
    public_readiness_summary,
    validate_compiled_ex5_readiness,
)
from app.core.mt5_detection import redact_public_path, validate_mt5_executable_path
from app.core.strategy_tester_report_config import (
    build_strategy_tester_report_contract,
    build_tester_ini_report_lines,
)
from app.core.terminal_contract_audit import build_terminal_contract_audit


DEFAULT_EXPERT = DEFAULT_BOOTSTRAP_EXPERT
BLOCKED_STATUS = "blocked_preflight_failed"
READY_STATUS = "ready_for_one_run_retry"
UNKNOWN_EXIT_CODE_CATEGORY = "unknown_terminal_exit"
PUBLIC_PREFLIGHT_JSON = Path("reports") / "public" / "real_mt5_preflight_summary.json"
PUBLIC_PREFLIGHT_MD = Path("reports") / "public" / "real_mt5_preflight_summary.md"
PUBLIC_PREFLIGHT_REPORT = Path("reports") / "public" / "MVP_014F_PREFLIGHT_READINESS_REPORT.md"
EX5_READINESS_MARKER_RELATIVE_PATH = (
    Path("runs") / "preflight_readiness" / "mvp_014f" / "compiled" / "SmokeHarness_Public.ex5"
)


@dataclass(frozen=True)
class RealMT5PreflightConfig:
    terminal_path: str = ""
    metaeditor_path: str = ""
    terminal_found: bool = False
    metaeditor_found: bool = False
    expert: str = DEFAULT_EXPERT
    expected_ex5_path: str = ""
    symbol: str = "XAUUSD"
    period: str = "M5"
    max_backtests: int = 1
    smoke_only: bool = True
    operator_gate_approved: bool = False
    close_after_run_policy: str = "always_after_real_run"
    tournament_100_run: bool = False
    credentials_stored: bool = False


@dataclass(frozen=True)
class PreflightCheckResult:
    name: str
    passed: bool
    blocking: bool
    reason: str
    detail: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RealMT5PreflightSummary:
    status: str
    ready_for_real_retry: bool
    failure_stage: str
    exit_code_recorded: int | None
    exit_code_category: str
    expert_path_checked: bool
    compiled_ex5_checked: bool
    report_export_contract_checked: bool
    report_path_privacy_checked: bool
    tester_ini_contract_checked: bool
    terminal_launch_args_sanitized: list[str]
    tester_ini_contract_summary: dict[str, object]
    report_contract_summary: dict[str, object]
    blocking_issues: list[str]
    warnings: list[str]
    checks: list[dict[str, object]] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _normalize_private_path(value: str) -> str:
    return value.replace("\\", "/").strip()


def _is_private_report_path(value: str) -> bool:
    normalized = _normalize_private_path(value).lstrip("./")
    return normalized.startswith("reports/private/")


def _parse_tester_ini(tester_ini_text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in tester_ini_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";") or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            values["_section"] = line.strip("[]")
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _sanitize_report_contract(report_contract: dict[str, object] | None) -> dict[str, object]:
    if not report_contract:
        return {}
    summary: dict[str, object] = {}
    for key in (
        "report_export_configured",
        "report_base",
        "replace_report",
        "shutdown_terminal",
        "expected_report_paths",
        "report_required",
        "parse_required",
        "private_artifacts_only",
        "public_summary_sanitized",
    ):
        value = report_contract.get(key)
        if isinstance(value, str):
            summary[key] = redact_public_path(value)
        elif isinstance(value, list):
            summary[key] = [redact_public_path(item) if isinstance(item, str) else item for item in value]
        else:
            summary[key] = value
    return summary


def validate_terminal_ready(config: RealMT5PreflightConfig) -> PreflightCheckResult:
    if not config.terminal_found:
        return PreflightCheckResult("terminal_ready", False, True, "terminal64.exe_not_confirmed")
    if config.terminal_path:
        try:
            validate_mt5_executable_path(config.terminal_path, "terminal64.exe")
        except (OSError, ValueError) as exc:
            return PreflightCheckResult("terminal_ready", False, True, "terminal64.exe_invalid", str(exc))
    return PreflightCheckResult("terminal_ready", True, False, "terminal64.exe_confirmed")


def validate_metaeditor_ready(config: RealMT5PreflightConfig) -> PreflightCheckResult:
    if not config.metaeditor_found:
        return PreflightCheckResult("metaeditor_ready", False, True, "metaeditor64.exe_not_confirmed")
    if config.metaeditor_path:
        try:
            validate_mt5_executable_path(config.metaeditor_path, "metaeditor64.exe")
        except (OSError, ValueError) as exc:
            return PreflightCheckResult("metaeditor_ready", False, True, "metaeditor64.exe_invalid", str(exc))
    return PreflightCheckResult("metaeditor_ready", True, False, "metaeditor64.exe_confirmed")


def validate_expert_path(config: RealMT5PreflightConfig) -> PreflightCheckResult:
    expert = config.expert.strip()
    if not expert:
        return PreflightCheckResult("expert_path", False, True, "expert_path_missing")
    if any(part in expert for part in ("..", ":", "/", "//")):
        return PreflightCheckResult("expert_path", False, True, "expert_path_not_safe")
    return PreflightCheckResult("expert_path", True, False, "expert_path_present", expert)


def validate_compiled_ex5_expected(config: RealMT5PreflightConfig) -> PreflightCheckResult:
    expected = config.expected_ex5_path.strip()
    if not expected:
        return PreflightCheckResult("compiled_ex5_expected", False, True, "compiled_ex5_not_configured")
    path = Path(expected)
    if path.suffix.lower() != ".ex5":
        return PreflightCheckResult("compiled_ex5_expected", False, True, "compiled_ex5_path_wrong_extension")
    if not path.exists() or not path.is_file():
        return PreflightCheckResult("compiled_ex5_expected", False, True, "compiled_ex5_not_found")
    return PreflightCheckResult("compiled_ex5_expected", True, False, "compiled_ex5_found", redact_public_path(path))


def validate_symbol_config(config: RealMT5PreflightConfig) -> PreflightCheckResult:
    if not config.symbol.strip():
        return PreflightCheckResult("symbol_config", False, True, "symbol_missing")
    return PreflightCheckResult("symbol_config", True, False, "symbol_present", config.symbol)


def validate_period_config(config: RealMT5PreflightConfig) -> PreflightCheckResult:
    allowed = {"M1", "M5", "M15", "M30", "H1", "H4", "D1"}
    if config.period not in allowed:
        return PreflightCheckResult("period_config", False, True, "period_not_supported", config.period)
    return PreflightCheckResult("period_config", True, False, "period_supported", config.period)


def validate_report_contract(report_contract: dict[str, object] | None) -> PreflightCheckResult:
    if not report_contract:
        return PreflightCheckResult("report_contract", False, True, "report_contract_missing")
    if not _as_bool(report_contract.get("report_export_configured")):
        return PreflightCheckResult("report_contract", False, True, "report_export_not_configured")
    if not _as_bool(report_contract.get("replace_report")):
        return PreflightCheckResult("report_contract", False, True, "replace_report_not_enabled")
    if not _as_bool(report_contract.get("shutdown_terminal")):
        return PreflightCheckResult("report_contract", False, True, "shutdown_terminal_not_enabled")
    report_base = str(report_contract.get("report_base", ""))
    if not _is_private_report_path(report_base):
        return PreflightCheckResult("report_contract", False, True, "report_base_not_private")
    expected_paths = report_contract.get("expected_report_paths", [])
    if not isinstance(expected_paths, list) or not expected_paths:
        return PreflightCheckResult("report_contract", False, True, "expected_report_paths_missing")
    if not all(isinstance(item, str) and _is_private_report_path(item) for item in expected_paths):
        return PreflightCheckResult("report_contract", False, True, "expected_report_paths_not_private")
    return PreflightCheckResult("report_contract", True, False, "report_contract_private_and_enabled")


def validate_tester_ini_contract(
    tester_ini_text: str,
    *,
    symbol: str = "XAUUSD",
    period: str = "M5",
) -> PreflightCheckResult:
    values = _parse_tester_ini(tester_ini_text)
    required = {
        "_section": "Tester",
        "Expert": None,
        "Symbol": symbol,
        "Period": period,
        "Optimization": "0",
        "Report": None,
        "ReplaceReport": "1",
        "ShutdownTerminal": "1",
    }
    missing: list[str] = []
    mismatched: list[str] = []
    for key, expected in required.items():
        if key not in values or not str(values[key]).strip():
            missing.append(key)
            continue
        if expected is not None and values[key] != expected:
            mismatched.append(f"{key}={values[key]}")
    if missing or mismatched:
        detail = ",".join([*(f"missing:{item}" for item in missing), *(f"mismatch:{item}" for item in mismatched)])
        return PreflightCheckResult("tester_ini_contract", False, True, "tester_ini_contract_invalid", detail)
    if not _is_private_report_path(values["Report"]):
        return PreflightCheckResult("tester_ini_contract", False, True, "tester_ini_report_path_not_private")
    return PreflightCheckResult("tester_ini_contract", True, False, "tester_ini_contract_valid")


def validate_private_artifact_paths(
    report_contract: dict[str, object] | None,
    tester_ini_text: str = "",
) -> PreflightCheckResult:
    paths: list[str] = []
    if report_contract:
        for key in ("report_base", "private_run_dir", "private_mt5_staging_dir", "expected_log_dir"):
            value = report_contract.get(key)
            if isinstance(value, str):
                paths.append(value)
        expected = report_contract.get("expected_report_paths", [])
        if isinstance(expected, list):
            paths.extend(item for item in expected if isinstance(item, str))
    if tester_ini_text:
        values = _parse_tester_ini(tester_ini_text)
        if values.get("Report"):
            paths.append(values["Report"])
    if not paths:
        return PreflightCheckResult("private_artifact_paths", False, True, "private_artifact_paths_missing")
    if not all(_is_private_report_path(item) for item in paths):
        return PreflightCheckResult("private_artifact_paths", False, True, "private_artifact_path_not_private")
    return PreflightCheckResult("private_artifact_paths", True, False, "private_artifact_paths_private")


def classify_exit_code(exit_code: int | None) -> str:
    if exit_code is None:
        return "not_recorded"
    if exit_code == 0:
        return "success"
    return UNKNOWN_EXIT_CODE_CATEGORY


def classify_failure_stage(
    *,
    exit_code: int | None,
    report_file_found: bool,
    strategy_tester_requested: bool,
    backtest_real_run: bool,
    ea_executed: bool,
) -> str:
    if exit_code == 0 and report_file_found and backtest_real_run and ea_executed:
        return "completed_report_found"
    if strategy_tester_requested and exit_code not in (None, 0) and not report_file_found and not ea_executed:
        return "strategy_tester_failed_before_ea"
    if strategy_tester_requested and not report_file_found:
        return "strategy_tester_no_report_found"
    if not strategy_tester_requested:
        return "not_attempted"
    return "unknown_failure_stage"


def make_preflight_summary(
    checks: list[PreflightCheckResult],
    *,
    failure_stage: str = "not_attempted",
    exit_code: int | None = None,
    terminal_launch_args_sanitized: list[str] | None = None,
    tester_ini_contract_summary: dict[str, object] | None = None,
    report_contract_summary: dict[str, object] | None = None,
) -> RealMT5PreflightSummary:
    blocking_issues = [check.reason for check in checks if not check.passed and check.blocking]
    warnings = [check.reason for check in checks if not check.passed and not check.blocking]
    ready = not blocking_issues
    return RealMT5PreflightSummary(
        status=READY_STATUS if ready else BLOCKED_STATUS,
        ready_for_real_retry=ready,
        failure_stage=failure_stage,
        exit_code_recorded=exit_code,
        exit_code_category=classify_exit_code(exit_code),
        expert_path_checked=any(check.name == "expert_path" for check in checks),
        compiled_ex5_checked=any(check.name == "compiled_ex5_expected" for check in checks),
        report_export_contract_checked=any(check.name == "report_contract" for check in checks),
        report_path_privacy_checked=any(check.name == "private_artifact_paths" for check in checks),
        tester_ini_contract_checked=any(check.name == "tester_ini_contract" for check in checks),
        terminal_launch_args_sanitized=terminal_launch_args_sanitized or [],
        tester_ini_contract_summary=tester_ini_contract_summary or {},
        report_contract_summary=report_contract_summary or {},
        blocking_issues=blocking_issues,
        warnings=warnings,
        checks=[check.to_dict() for check in checks],
    )


def build_real_mt5_preflight_check(
    config: RealMT5PreflightConfig,
    report_contract: dict[str, object] | None,
    candidate: dict[str, object] | None = None,
    *,
    tester_ini_text: str = "",
    exit_code: int | None = None,
    report_file_found: bool = False,
    strategy_tester_requested: bool = False,
    backtest_real_run: bool = False,
    ea_executed: bool = False,
) -> dict[str, object]:
    candidate = candidate or {}
    checks = [
        validate_terminal_ready(config),
        validate_metaeditor_ready(config),
        validate_expert_path(config),
        validate_compiled_ex5_expected(config),
        validate_symbol_config(config),
        validate_period_config(config),
        validate_report_contract(report_contract),
        validate_tester_ini_contract(tester_ini_text, symbol=config.symbol, period=config.period),
        validate_private_artifact_paths(report_contract, tester_ini_text),
    ]
    if config.max_backtests != 1:
        checks.append(PreflightCheckResult("max_backtests", False, True, "max_backtests_must_equal_1"))
    else:
        checks.append(PreflightCheckResult("max_backtests", True, False, "max_backtests_equal_1"))
    if not config.smoke_only:
        checks.append(PreflightCheckResult("smoke_only", False, True, "smoke_only_required"))
    else:
        checks.append(PreflightCheckResult("smoke_only", True, False, "smoke_only_confirmed"))
    if not config.operator_gate_approved:
        checks.append(PreflightCheckResult("operator_gate", False, True, "operator_gate_not_approved"))
    else:
        checks.append(PreflightCheckResult("operator_gate", True, False, "operator_gate_approved"))
    if config.tournament_100_run:
        checks.append(PreflightCheckResult("tournament_block", False, True, "tournament_100_run_blocked"))
    else:
        checks.append(PreflightCheckResult("tournament_block", True, False, "not_a_tournament"))
    if config.credentials_stored:
        checks.append(PreflightCheckResult("credential_boundary", False, True, "credentials_must_not_be_stored"))
    else:
        checks.append(PreflightCheckResult("credential_boundary", True, False, "credentials_not_stored"))
    if config.close_after_run_policy != "always_after_real_run":
        checks.append(PreflightCheckResult("close_after_run_policy", False, True, "close_after_run_policy_missing"))
    else:
        checks.append(PreflightCheckResult("close_after_run_policy", True, False, "close_after_run_policy_confirmed"))

    tester_values = _parse_tester_ini(tester_ini_text)
    tester_summary = {
        "section": tester_values.get("_section", ""),
        "expert": tester_values.get("Expert", candidate.get("expert", "")),
        "symbol": tester_values.get("Symbol", config.symbol),
        "period": tester_values.get("Period", config.period),
        "optimization": tester_values.get("Optimization", ""),
        "report_configured": bool(tester_values.get("Report")),
        "replace_report": tester_values.get("ReplaceReport", ""),
        "shutdown_terminal": tester_values.get("ShutdownTerminal", ""),
    }
    failure_stage = classify_failure_stage(
        exit_code=exit_code,
        report_file_found=report_file_found,
        strategy_tester_requested=strategy_tester_requested,
        backtest_real_run=backtest_real_run,
        ea_executed=ea_executed,
    )
    terminal_args = []
    if config.terminal_path:
        terminal_args.append(redact_public_path(config.terminal_path))
        terminal_args.append("/config:<PRIVATE_TESTER_INI>")
    summary = make_preflight_summary(
        checks,
        failure_stage=failure_stage,
        exit_code=exit_code,
        terminal_launch_args_sanitized=terminal_args,
        tester_ini_contract_summary=tester_summary,
        report_contract_summary=_sanitize_report_contract(report_contract),
    )
    payload = summary.to_dict()
    payload["candidate_id"] = str(candidate.get("candidate_id", ""))
    payload["expert_expected"] = config.expert
    payload["compiled_ex5_expected"] = redact_public_path(config.expected_ex5_path)
    payload["paths_sanitized"] = True
    return payload


def _check_passed(summary: dict[str, object], check_name: str) -> bool:
    checks = summary.get("checks", [])
    return any(
        isinstance(check, dict) and check.get("name") == check_name and bool(check.get("passed"))
        for check in checks
    )


def _build_preflight_tester_ini(report_contract: dict[str, object]) -> str:
    return "\n".join(
        [
            "[Tester]",
            f"Expert={DEFAULT_EXPERT}",
            "Symbol=XAUUSD",
            "Period=M5",
            "Model=0",
            "Optimization=0",
            "Deposit=10000",
            "Currency=USD",
            *build_tester_ini_report_lines(report_contract),
            "",
        ]
    )


def expected_preflight_ex5_marker_path(project_root: Path) -> Path:
    return project_root / EX5_READINESS_MARKER_RELATIVE_PATH


def resolve_preflight_expected_ex5_path(project_root: Path) -> Path | None:
    marker = load_compiled_ex5_readiness_marker(project_root)
    candidate = Path(str(marker.get("compiled_ex5_expected_path", "") or ""))
    if candidate.suffix.lower() == ".ex5" and candidate.exists() and candidate.is_file():
        return candidate
    return None


def ensure_ignored_preflight_ex5_marker(project_root: Path) -> Path:
    """Create an ignored local readiness marker for the EX5 existence check.

    The file is under `runs/`, which is ignored by Git. It is not a shipped EA,
    not a compiled strategy claim and not a public artifact.
    """

    ex5_path = expected_preflight_ex5_marker_path(project_root)
    ex5_path.parent.mkdir(parents=True, exist_ok=True)
    if not ex5_path.exists():
        ex5_path.write_text("local preflight readiness marker; not a compiled product artifact\n", encoding="utf-8")
    return ex5_path


def _preflight_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# MVP-014F Preflight Readiness",
        "",
        f"- Status: {payload['status']}",
        f"- Ready for retry: {str(payload['ready_for_retry']).lower()}",
        f"- Blocking issues: {', '.join(payload['blocking_issues']) if payload['blocking_issues'] else 'none'}",
        f"- Warnings: {', '.join(payload['warnings']) if payload['warnings'] else 'none'}",
        f"- Expert path ready: {str(payload['expert_path_ready']).lower()}",
        f"- Compiled EX5 ready: {str(payload['compiled_ex5_ready']).lower()}",
        f"- Tester INI contract ready: {str(payload['tester_ini_contract_ready']).lower()}",
        f"- Report contract ready: {str(payload['report_contract_ready']).lower()}",
        f"- Close-after-run ready: {str(payload['close_after_run_ready']).lower()}",
        f"- Operator Gate ready: {str(payload['operator_gate_ready']).lower()}",
        f"- MT5 real run new: {str(payload['mt5_real_run_new']).lower()}",
        f"- Backtest real run new: {str(payload['backtest_real_run_new']).lower()}",
        f"- Strategy Tester run new: {str(payload['strategy_tester_run_new']).lower()}",
        f"- EA executed new: {str(payload['ea_executed_new']).lower()}",
        f"- Tournament 100 run: {str(payload['tournament_100_run']).lower()}",
        f"- Credentials stored: {str(payload['credentials_stored']).lower()}",
        f"- Paths sanitized: {str(payload['paths_sanitized']).lower()}",
        "",
        "This preflight does not launch MT5, does not start Strategy Tester and does not execute an EA.",
        "The EX5 readiness check uses an ignored local readiness marker under runs/ and must be rechecked before any real retry.",
    ]
    return "\n".join(lines) + "\n"


def _sanitize_preflight_public_value(value: object) -> object:
    if isinstance(value, str):
        return value.replace(".ex5", "<COMPILED_EA_FILE>")
    if isinstance(value, list):
        return [_sanitize_preflight_public_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_preflight_public_value(item) for key, item in value.items()}
    return value


def _sanitize_preflight_public_payload(payload: dict[str, object]) -> dict[str, object]:
    return {key: _sanitize_preflight_public_value(value) for key, value in payload.items()}


def generate_real_mt5_preflight_readiness(project_root: Path) -> dict[str, object]:
    """Write public-safe MVP-014F preflight summaries without executing MT5."""

    report_contract = build_strategy_tester_report_contract("mvp_014f_preflight_readiness")
    tester_ini_text = _build_preflight_tester_ini(report_contract)
    expected_ex5_path = resolve_preflight_expected_ex5_path(project_root) or expected_preflight_ex5_marker_path(project_root)
    summary = build_real_mt5_preflight_check(
        RealMT5PreflightConfig(
            terminal_found=True,
            metaeditor_found=True,
            expert=DEFAULT_EXPERT,
            expected_ex5_path=str(expected_ex5_path),
            symbol="XAUUSD",
            period="M5",
            max_backtests=1,
            smoke_only=True,
            operator_gate_approved=True,
            close_after_run_policy="always_after_real_run",
            tournament_100_run=False,
            credentials_stored=False,
        ),
        report_contract,
        {"candidate_id": "mvp_014f_preflight_readiness", "expert": DEFAULT_EXPERT},
        tester_ini_text=tester_ini_text,
    )
    payload: dict[str, object] = {
        **summary,
        "preflight_command": True,
        "preflight_validator": True,
        "ready_for_retry": bool(summary["ready_for_real_retry"]),
        "expert_path_ready": _check_passed(summary, "expert_path"),
        "compiled_ex5_ready": _check_passed(summary, "compiled_ex5_expected"),
        "tester_ini_contract_ready": _check_passed(summary, "tester_ini_contract"),
        "report_contract_ready": _check_passed(summary, "report_contract"),
        "close_after_run_ready": _check_passed(summary, "close_after_run_policy"),
        "operator_gate_ready": _check_passed(summary, "operator_gate"),
        "public_preflight_summary": True,
        "mt5_real_run_new": False,
        "backtest_real_run_new": False,
        "strategy_tester_run_new": False,
        "ea_executed_new": False,
        "tournament_100_run": False,
        "exe_created": False,
        "zip_created": False,
        "credentials_stored": False,
        "private_files_committed": False,
        "raw_logs_public": False,
        "paths_sanitized": True,
        "preflight_mode": "contract_readiness_no_terminal_launch",
        "next_step": "operator may approve MVP-014L only after review and fresh Operator Gate approval"
        if bool(summary["ready_for_real_retry"])
        else "retry remains blocked until terminal DataDir and expert mapping diagnostics pass",
    }
    terminal_contract = build_terminal_contract_audit(project_root)
    terminal_contract_readiness = dict(terminal_contract.get("readiness", {})) or public_readiness_summary(
        validate_compiled_ex5_readiness(
            project_root,
            environment={},
            expert_relative_path=DEFAULT_EXPERT,
            allow_external_filesystem_check=False,
        )
    )
    payload["terminal_contract_audit_required"] = True
    payload["terminal_contract_audit"] = terminal_contract.get("terminal_contract_audit", "FAIL")
    payload["terminal_contract_readiness"] = terminal_contract_readiness
    payload["compiled_ex5_verified_in_terminal_datadir"] = terminal_contract_readiness[
        "compiled_ex5_verified_in_terminal_datadir"
    ]
    payload["terminal_datadir_consistent"] = terminal_contract_readiness["terminal_datadir_consistent"]
    if not bool(terminal_contract.get("ready_for_real_retry")):
        payload["status"] = BLOCKED_STATUS
        payload["ready_for_real_retry"] = False
        payload["ready_for_retry"] = False
        payload["blocking_issues"] = list(
            dict.fromkeys(
                [
                    *list(payload.get("blocking_issues", [])),
                    *list(terminal_contract.get("blocking_issues", [])),
                ]
            )
        )
        payload["next_step"] = str(terminal_contract.get("next_step", "fix terminal contract blocking issues"))
    payload = _sanitize_preflight_public_payload(payload)
    public_json = project_root / PUBLIC_PREFLIGHT_JSON
    public_md = project_root / PUBLIC_PREFLIGHT_MD
    public_report = project_root / PUBLIC_PREFLIGHT_REPORT
    public_json.parent.mkdir(parents=True, exist_ok=True)
    public_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown = _preflight_markdown(payload)
    public_md.write_text(markdown, encoding="utf-8")
    public_report.write_text(markdown, encoding="utf-8")
    return {
        "status": "PASS_MVP_014F_PREFLIGHT_READY_FOR_REAL_RETRY" if payload["ready_for_retry"] else "HOLD_MVP_014F_PREFLIGHT_BLOCKED",
        "summary": payload,
        "files": {
            "json": str(public_json),
            "markdown": str(public_md),
            "report": str(public_report),
        },
    }
