#!/usr/bin/env python3
"""MT5 Robot Lab desktop bootstrap."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.app_config import load_app_config, validate_app_config
from app.core.candidate_generator import DEFAULT_SEED, generate_candidates, save_candidates
from app.core.candidate_runner import run_xauusd_base_seed_smoke
from app.core.champion_dna import (
    ChampionDNA,
    hash_source_text,
    make_public_champion_summary,
    parameter_diff,
    sample_champion_dna,
    save_champion_dna,
    validate_champion_dna,
    write_champion_artifacts,
)
from app.core.export_reports import export_sample_summary
from app.core.intelligence_modes import validate_intelligence_modes
from app.core.lab_registry import load_lab_registry
from app.core.leaderboard_schema import make_public_leaderboard_sample, validate_leaderboard_entry
from app.core.mt5_detection import generate_diagnostics, write_local_mt5_environment_status
from app.core.operator_gate import (
    APPROVAL_PHRASE_EN,
    APPROVAL_PHRASE_PT,
    approve_operator_gate,
    create_operator_approval_request,
    default_operator_gate,
    is_real_mt5_execution_allowed,
    make_operator_gate_summary,
    write_operator_gate_preview,
)
from app.core.real_mt5_preflight import generate_real_mt5_preflight_readiness
from app.core.real_mt5_runtime_contract import generate_real_mt5_runtime_dry_run
from app.core.real_mt5_smoke import execute_one_run_real_mt5_smoke
from app.core.risk_profile_ranking import generate_risk_profile_report
from app.core.symbol_mapping import TIMEFRAME_MINUTES
from app.core.submission_package import create_submission_package, validate_submission_package
from app.core.tournament_engine import run_tournament
from app.ui.main_window import launch_app
from app.ui.screens import INTELLIGENCE_MODE_OPTIONS, NavigationController, build_screen_registry


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _self_test_root(name: str) -> Path:
    root = PROJECT_ROOT / "runs" / "self_tests" / name
    root.mkdir(parents=True, exist_ok=True)
    return root


def _self_test_public_root(name: str) -> Path:
    public_root = _self_test_root(name) / "reports" / "public"
    public_root.mkdir(parents=True, exist_ok=True)
    return public_root


def run_self_test() -> dict[str, object]:
    public_root = _self_test_public_root("app_self_test")
    config = load_app_config(PROJECT_ROOT / "config" / "app.default.json")
    validate_app_config(config)
    validate_intelligence_modes(config.supported_intelligence_modes, config.default_intelligence_mode)
    if config.default_timeframe not in TIMEFRAME_MINUTES:
        raise AssertionError("Default timeframe is not supported")

    screens = build_screen_registry(config)
    if len(screens) != 12:
        raise AssertionError("Desktop navigation must expose 12 screens")
    controller = NavigationController(screens)
    if controller.current_screen != "welcome":
        raise AssertionError("Default screen must be welcome")
    if controller.next_screen().id != "lab_selection":
        raise AssertionError("next_screen did not advance to lab_selection")
    if controller.previous_screen().id != "welcome":
        raise AssertionError("previous_screen did not return to welcome")
    if controller.go_to_screen("settings").id != "settings":
        raise AssertionError("go_to_screen did not navigate to settings")
    if controller.go_to_screen("real_mt5_smoke_gate").id != "real_mt5_smoke_gate":
        raise AssertionError("go_to_screen did not navigate to real_mt5_smoke_gate")
    if {option["mode"] for option in INTELLIGENCE_MODE_OPTIONS} != {"local_auto", "codex_assisted", "seeds_only"}:
        raise AssertionError("Intelligence mode screen must contain exactly 3 modes")

    labs = load_lab_registry(PROJECT_ROOT / "config" / "labs.example.json")
    if not labs:
        raise AssertionError("At least one lab example is required")

    dna = sample_champion_dna()
    if not isinstance(dna, ChampionDNA):
        raise AssertionError("Champion DNA sample did not build")
    validate_champion_dna(dna)
    if len(hash_source_text("sample")) != 64:
        raise AssertionError("Champion DNA hash_source_text must return SHA-256 hex")
    diff = parameter_diff({"ATR_period": 14}, {"ATR_period": 21})
    if diff[0]["parameter"] != "ATR_period":
        raise AssertionError("Champion DNA parameter_diff did not report ATR_period")
    public_summary = make_public_champion_summary(dna)
    if "password" in public_summary.lower() or "token" in public_summary.lower():
        raise AssertionError("Champion DNA public summary contains sensitive text")
    if dna.risk_mode != "wild" or dna.max_drawdown_tolerated_pct != 100.0:
        raise AssertionError("Champion DNA sample must cover wild risk mode")

    artifact_root = public_root / "sample_champion_dna"
    written = write_champion_artifacts(dna, artifact_root)
    dna_v2_artifacts = save_champion_dna(dna, public_root)
    submission_package = create_submission_package(
        dna,
        {
            "status": "sample_not_real_backtest",
            "ranking_metric": "profit",
            "candidate_count": 1,
        },
        {
            "lab_id": "ea-xau",
            "lab_name": "XAU Robot Lab",
            "requested_symbol": "XAUUSD",
            "broker_symbol": "XAUUSD",
            "timeframe": "M5",
            "timeframe_minutes": 5,
            "initial_balance_usd": 10000.0,
        },
        public_root / "submission_package_sample",
    )
    validation = validate_submission_package(public_root / "submission_package_sample")
    if validation["validation_status"] != "pass":
        raise AssertionError("Submission package validation failed")
    leaderboard_sample = make_public_leaderboard_sample(public_root)
    if leaderboard_sample["mt5_real_run"] or leaderboard_sample["backtest_real_run"] or leaderboard_sample["upload_ready"]:
        raise AssertionError("Leaderboard sample must remain non-real and not upload-ready")
    validate_leaderboard_entry(leaderboard_sample["entries"][0])
    operator_gate = default_operator_gate()
    if is_real_mt5_execution_allowed(operator_gate):
        raise AssertionError("Default operator gate must block real MT5 execution")
    wrong_phrase = approve_operator_gate(operator_gate, "wrong phrase")
    if wrong_phrase["approval_phrase_matched"] or wrong_phrase["execution_allowed"]:
        raise AssertionError("Wrong operator approval phrase must not approve execution")
    technical_ready_request = create_operator_approval_request(
        {
            "real_execution_requested": True,
            "smoke_only": True,
            "max_backtests": 1,
            "tournament_100_run": False,
            "credentials_stored": False,
        },
        {
            "mt5_installed": True,
            "terminal_found": True,
            "metaeditor_found": True,
        },
    )
    approved_gate = approve_operator_gate(technical_ready_request, APPROVAL_PHRASE_EN)
    if not approved_gate["execution_allowed"]:
        raise AssertionError("Correct phrase and technical readiness should approve the gate")
    too_many = create_operator_approval_request(
        {"real_execution_requested": True, "max_backtests": 2},
        {"mt5_installed": True, "terminal_found": True, "metaeditor_found": True},
    )
    if approve_operator_gate(too_many, APPROVAL_PHRASE_PT)["execution_allowed"]:
        raise AssertionError("Operator gate must block max_backtests > 1")
    tournament_100 = create_operator_approval_request(
        {"real_execution_requested": True, "tournament_100_run": True},
        {"mt5_installed": True, "terminal_found": True, "metaeditor_found": True},
    )
    if approve_operator_gate(tournament_100, APPROVAL_PHRASE_EN)["execution_allowed"]:
        raise AssertionError("Operator gate must block tournament_100_run=true")
    credentials = create_operator_approval_request(
        {"real_execution_requested": True, "credentials_stored": True},
        {"mt5_installed": True, "terminal_found": True, "metaeditor_found": True},
    )
    if approve_operator_gate(credentials, APPROVAL_PHRASE_EN)["execution_allowed"]:
        raise AssertionError("Operator gate must block stored credentials")
    exports = export_sample_summary(public_root)

    return {
        "self_test": "passed",
        "product_name": config.product_name,
        "default_lab": config.default_lab,
        "default_screen": screens[0].id,
        "labs_loaded": [lab.id for lab in labs],
        "screens": [screen.id for screen in screens],
        "real_mt5_required": False,
        "gui_required_for_self_test": False,
        "codex_required": config.codex_required,
        "champion_artifacts": {key: str(value) for key, value in written.items()},
        "champion_dna_v2": {key: str(value) for key, value in dna_v2_artifacts.items()},
        "submission_package": submission_package,
        "leaderboard_sample": {
            "status": leaderboard_sample["status"],
            "entry_count": len(leaderboard_sample["entries"]),
            "mt5_real_run": leaderboard_sample["mt5_real_run"],
            "backtest_real_run": leaderboard_sample["backtest_real_run"],
            "upload_ready": leaderboard_sample["upload_ready"],
        },
        "operator_gate": make_operator_gate_summary(operator_gate),
        "exports": {key: str(value) for key, value in exports.items()},
    }


def run_operator_gate_self_test() -> dict[str, object]:
    gate = default_operator_gate()
    wrong_phrase = approve_operator_gate(gate, "wrong phrase")
    technical_ready = create_operator_approval_request(
        {
            "real_execution_requested": True,
            "smoke_only": True,
            "max_backtests": 1,
            "tournament_100_run": False,
            "credentials_stored": False,
        },
        {
            "mt5_installed": True,
            "terminal_found": True,
            "metaeditor_found": True,
        },
    )
    approved = approve_operator_gate(technical_ready, APPROVAL_PHRASE_EN)
    return {
        "status": "operator_gate_self_test_passed",
        "default_blocks": not gate["execution_allowed"],
        "wrong_phrase_blocks": not wrong_phrase["execution_allowed"],
        "correct_phrase_can_approve_when_ready": approved["execution_allowed"],
        "mt5_real_run": False,
        "backtest_real_run": False,
        "credentials_stored": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MT5 Robot Lab")
    parser.add_argument("--self-test", action="store_true", help="Run non-GUI validation")
    parser.add_argument("--mt5-self-test", action="store_true", help="Run safe MT5 detection diagnostics")
    parser.add_argument("--backtest-smoke-self-test", action="store_true", help="Write one safe smoke backtest result")
    parser.add_argument("--candidate-generator-self-test", action="store_true", help="Generate safe candidate JSON artifacts")
    parser.add_argument("--tournament-smoke-self-test", action="store_true", help="Run the safe MVP-006 tournament smoke")
    parser.add_argument("--risk-profile-self-test", action="store_true", help="Rank tournament candidates by risk profile")
    parser.add_argument("--operator-gate-self-test", action="store_true", help="Run safe operator gate validation")
    parser.add_argument("--preview-real-mt5-smoke-gate", action="store_true", help="Write safe operator gate preview artifacts")
    parser.add_argument("--detect-mt5-local", action="store_true", help="Write safe local MT5 environment verification")
    parser.add_argument("--real-mt5-preflight", action="store_true", help="Write safe real MT5 retry preflight readiness")
    parser.add_argument(
        "--real-mt5-runtime-dry-run",
        action="store_true",
        help="Validate the real MT5 runtime contract without launching MT5",
    )
    parser.add_argument("--run-real-mt5-smoke", action="store_true", help="Run one explicitly approved local MT5 smoke")
    parser.add_argument("--operator-approval-phrase", default="", help="Exact operator approval phrase for real smoke")
    parser.add_argument("--mt5-terminal-path", default="", help="Optional manual terminal64.exe path for safe detection only")
    parser.add_argument("--mt5-metaeditor-path", default="", help="Optional manual metaeditor64.exe path for safe detection only")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        print(json.dumps(run_self_test(), indent=2, sort_keys=True))
        return 0
    if args.mt5_self_test:
        result = generate_diagnostics(_self_test_public_root("mt5_diagnostics"))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.backtest_smoke_self_test:
        result = run_xauusd_base_seed_smoke(_self_test_public_root("backtest_smoke"), allow_real_execution=False)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.candidate_generator_self_test:
        candidates = generate_candidates(DEFAULT_SEED)
        result = save_candidates(candidates, _self_test_root("candidate_generator") / "candidates")
        print(
            json.dumps(
                {
                    "status": "OK",
                    "candidate_count": len(result.candidates),
                    "files": result.files,
                    "log_path": result.log_path,
                    "mt5_real_run": False,
                    "backtest_run": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.tournament_smoke_self_test:
        result = run_tournament(_self_test_root("tournament_smoke"))
        print(json.dumps(result.__dict__, indent=2, sort_keys=True))
        return 0
    if args.risk_profile_self_test:
        risk_root = _self_test_root("risk_profile")
        run_tournament(risk_root)
        result = generate_risk_profile_report(
            risk_root / "reports" / "public" / "tournament_ranking.json",
            risk_root / "reports" / "public" / "risk_profile_ranking.json",
        )
        print(json.dumps(result.__dict__, indent=2, sort_keys=True))
        return 0
    if args.operator_gate_self_test:
        print(json.dumps(run_operator_gate_self_test(), indent=2, sort_keys=True))
        return 0
    if args.preview_real_mt5_smoke_gate:
        preview = write_operator_gate_preview(_self_test_public_root("operator_gate_preview"))
        print(json.dumps(preview, indent=2, sort_keys=True))
        return 0
    if args.detect_mt5_local:
        result = write_local_mt5_environment_status(
            PROJECT_ROOT / "reports" / "public",
            terminal_path=args.mt5_terminal_path or None,
            metaeditor_path=args.mt5_metaeditor_path or None,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.real_mt5_preflight:
        result = generate_real_mt5_preflight_readiness(PROJECT_ROOT)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.real_mt5_runtime_dry_run:
        result = generate_real_mt5_runtime_dry_run(PROJECT_ROOT)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.run_real_mt5_smoke:
        result = execute_one_run_real_mt5_smoke(PROJECT_ROOT, approval_phrase=args.operator_approval_phrase)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    launch_app(PROJECT_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
