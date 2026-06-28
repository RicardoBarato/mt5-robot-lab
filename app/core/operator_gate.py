"""Explicit operator gate for future real MT5 smoke execution.

The gate records approval state only. It does not launch MT5, does not start
Strategy Tester and does not store broker credentials.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


APPROVAL_PHRASE_EN = "I understand this will attempt one local MT5 smoke run only"
APPROVAL_PHRASE_PT = "Eu entendo que isso tentara apenas um smoke local do MT5"
BLOCKED_REASON = "Real MT5 smoke execution requires explicit operator approval."

REQUIRED_GATE_FIELDS = {
    "operator_confirmed",
    "mt5_detected",
    "terminal_found",
    "metaeditor_found",
    "real_execution_requested",
    "smoke_only",
    "max_backtests",
    "tournament_100_run",
    "no_credentials_stored",
    "approval_phrase_matched",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if value is None:
        return {}
    return {key: getattr(value, key) for key in dir(value) if not key.startswith("_") and not callable(getattr(value, key))}


def _approval_phrase_matches(approval_phrase: str) -> bool:
    normalized = " ".join(approval_phrase.strip().split()).lower()
    accepted = {
        APPROVAL_PHRASE_EN.lower(),
        APPROVAL_PHRASE_PT.lower(),
    }
    return normalized in accepted


def default_operator_gate() -> dict[str, Any]:
    return {
        "status": "blocked_by_operator_gate",
        "created_at": _utc_now(),
        "operator_confirmed": False,
        "mt5_detected": False,
        "terminal_found": False,
        "metaeditor_found": False,
        "real_execution_requested": False,
        "smoke_only": True,
        "max_backtests": 1,
        "tournament_100_run": False,
        "no_credentials_stored": True,
        "approval_phrase_matched": False,
        "execution_allowed": False,
        "mt5_real_run": False,
        "backtest_real_run": False,
        "strategy_tester_run": False,
        "reason": BLOCKED_REASON,
    }


def create_operator_approval_request(config: Any, mt5_diagnostics: Any) -> dict[str, Any]:
    config_data = _as_dict(config)
    diagnostics = _as_dict(mt5_diagnostics)
    gate = default_operator_gate()
    terminal_found = bool(diagnostics.get("terminal_found") or diagnostics.get("terminal_detected"))
    metaeditor_found = bool(diagnostics.get("metaeditor_found") or diagnostics.get("metaeditor_detected"))
    gate.update(
        {
            "request_id": config_data.get("request_id", f"operator_gate_{_utc_now()}"),
            "requested_symbol": config_data.get("symbol", config_data.get("requested_symbol", "XAUUSD")),
            "timeframe": config_data.get("timeframe", "M5"),
            "mt5_detected": bool(diagnostics.get("mt5_installed") or (terminal_found and metaeditor_found)),
            "terminal_found": terminal_found,
            "metaeditor_found": metaeditor_found,
            "real_execution_requested": bool(config_data.get("real_execution_requested", False)),
            "smoke_only": bool(config_data.get("smoke_only", True)),
            "max_backtests": int(config_data.get("max_backtests", 1) or 1),
            "tournament_100_run": bool(config_data.get("tournament_100_run", False)),
            "no_credentials_stored": not bool(config_data.get("credentials_stored", False)),
        }
    )
    return validate_operator_approval_request(gate)


def validate_operator_approval_request(request: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(REQUIRED_GATE_FIELDS - set(request))
    if missing:
        raise ValueError(f"Operator gate request missing fields: {missing}")
    gate = deepcopy(request)
    gate["execution_allowed"] = is_real_mt5_execution_allowed(gate)
    gate["status"] = "operator_gate_approved" if gate["execution_allowed"] else "blocked_by_operator_gate"
    gate["reason"] = "approved_for_one_local_mt5_smoke_only" if gate["execution_allowed"] else BLOCKED_REASON
    gate["mt5_real_run"] = False
    gate["backtest_real_run"] = False
    gate["strategy_tester_run"] = False
    return gate


def approve_operator_gate(request: dict[str, Any], approval_phrase: str) -> dict[str, Any]:
    gate = deepcopy(request)
    gate["operator_confirmed"] = True
    gate["approval_phrase_matched"] = _approval_phrase_matches(approval_phrase)
    gate["approved_at"] = _utc_now() if gate["approval_phrase_matched"] else ""
    return validate_operator_approval_request(gate)


def reject_operator_gate(request: dict[str, Any], reason: str) -> dict[str, Any]:
    gate = deepcopy(request)
    gate["operator_confirmed"] = False
    gate["approval_phrase_matched"] = False
    gate["execution_allowed"] = False
    gate["status"] = "operator_gate_rejected"
    gate["reason"] = reason or BLOCKED_REASON
    gate["mt5_real_run"] = False
    gate["backtest_real_run"] = False
    gate["strategy_tester_run"] = False
    return gate


def is_real_mt5_execution_allowed(gate_state: dict[str, Any]) -> bool:
    return all(
        [
            bool(gate_state.get("operator_confirmed")),
            bool(gate_state.get("mt5_detected")),
            bool(gate_state.get("terminal_found")),
            bool(gate_state.get("metaeditor_found")),
            bool(gate_state.get("real_execution_requested")),
            bool(gate_state.get("smoke_only")),
            int(gate_state.get("max_backtests", 0) or 0) == 1,
            not bool(gate_state.get("tournament_100_run")),
            bool(gate_state.get("no_credentials_stored")),
            bool(gate_state.get("approval_phrase_matched")),
        ]
    )


def make_operator_gate_summary(gate_state: dict[str, Any]) -> dict[str, Any]:
    gate = validate_operator_approval_request(gate_state)
    return {
        "status": gate["status"],
        "execution_allowed": gate["execution_allowed"],
        "mt5_detected": gate["mt5_detected"],
        "terminal_found": gate["terminal_found"],
        "metaeditor_found": gate["metaeditor_found"],
        "operator_confirmed": gate["operator_confirmed"],
        "smoke_only": gate["smoke_only"],
        "max_backtests": gate["max_backtests"],
        "tournament_100_run": gate["tournament_100_run"],
        "no_credentials_stored": gate["no_credentials_stored"],
        "approval_phrase_matched": gate["approval_phrase_matched"],
        "mt5_real_run": False,
        "backtest_real_run": False,
        "reason": gate["reason"],
    }


def save_operator_gate_manifest(gate_state: dict[str, Any], path: Path) -> dict[str, Any]:
    manifest = validate_operator_approval_request(gate_state)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def load_operator_gate_manifest(path: Path) -> dict[str, Any]:
    return validate_operator_approval_request(json.loads(path.read_text(encoding="utf-8")))


def _operator_gate_markdown(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Real MT5 Smoke Gate Preview",
            "",
            f"- Status: {summary['status']}",
            f"- Execution allowed: {str(summary['execution_allowed']).lower()}",
            f"- MT5 detected: {str(summary['mt5_detected']).lower()}",
            f"- Terminal found: {str(summary['terminal_found']).lower()}",
            f"- MetaEditor found: {str(summary['metaeditor_found']).lower()}",
            f"- Operator confirmed: {str(summary['operator_confirmed']).lower()}",
            f"- Smoke only: {str(summary['smoke_only']).lower()}",
            f"- Max backtests: {summary['max_backtests']}",
            f"- Tournament 100 run: {str(summary['tournament_100_run']).lower()}",
            "- MT5 real run: false",
            "- Backtest real run: false",
            "",
            "This preview does not launch MT5, does not run Strategy Tester and does not store credentials.",
        ]
    ) + "\n"


def write_operator_gate_preview(output_dir: Path, gate_state: dict[str, Any] | None = None) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    gate = gate_state or default_operator_gate()
    manifest_path = output_dir / "operator_gate_preview.json"
    markdown_path = output_dir / "operator_gate_preview.md"
    manifest = save_operator_gate_manifest(gate, manifest_path)
    summary = make_operator_gate_summary(manifest)
    markdown_path.write_text(_operator_gate_markdown(summary), encoding="utf-8")
    return {
        "status": summary["status"],
        "execution_allowed": summary["execution_allowed"],
        "mt5_real_run": False,
        "backtest_real_run": False,
        "files": {
            "json": str(manifest_path),
            "markdown": str(markdown_path),
        },
        "summary": summary,
    }
