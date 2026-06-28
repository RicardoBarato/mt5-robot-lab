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
from app.core.champion_dna import ChampionDNA, sample_champion_dna, write_champion_artifacts
from app.core.export_reports import export_sample_summary
from app.core.intelligence_modes import validate_intelligence_modes
from app.core.lab_registry import load_lab_registry
from app.core.mt5_detection import generate_diagnostics
from app.core.risk_profile_ranking import generate_risk_profile_report
from app.core.symbol_mapping import TIMEFRAME_MINUTES
from app.core.tournament_engine import run_tournament
from app.ui.main_window import launch_app
from app.ui.screens import INTELLIGENCE_MODE_OPTIONS, NavigationController, build_screen_registry


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_self_test() -> dict[str, object]:
    config = load_app_config(PROJECT_ROOT / "config" / "app.default.json")
    validate_app_config(config)
    validate_intelligence_modes(config.supported_intelligence_modes, config.default_intelligence_mode)
    if config.default_timeframe not in TIMEFRAME_MINUTES:
        raise AssertionError("Default timeframe is not supported")

    screens = build_screen_registry(config)
    if len(screens) != 11:
        raise AssertionError("Desktop navigation must expose 11 screens")
    controller = NavigationController(screens)
    if controller.current_screen != "welcome":
        raise AssertionError("Default screen must be welcome")
    if controller.next_screen().id != "lab_selection":
        raise AssertionError("next_screen did not advance to lab_selection")
    if controller.previous_screen().id != "welcome":
        raise AssertionError("previous_screen did not return to welcome")
    if controller.go_to_screen("settings").id != "settings":
        raise AssertionError("go_to_screen did not navigate to settings")
    if {option["mode"] for option in INTELLIGENCE_MODE_OPTIONS} != {"local_auto", "codex_assisted", "seeds_only"}:
        raise AssertionError("Intelligence mode screen must contain exactly 3 modes")

    labs = load_lab_registry(PROJECT_ROOT / "config" / "labs.example.json")
    if not labs:
        raise AssertionError("At least one lab example is required")

    dna = sample_champion_dna()
    if not isinstance(dna, ChampionDNA):
        raise AssertionError("Champion DNA sample did not build")

    artifact_root = PROJECT_ROOT / "reports" / "public" / "sample_champion_dna"
    written = write_champion_artifacts(dna, artifact_root)
    exports = export_sample_summary(PROJECT_ROOT / "reports" / "public")

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
        "exports": {key: str(value) for key, value in exports.items()},
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MT5 Robot Lab")
    parser.add_argument("--self-test", action="store_true", help="Run non-GUI validation")
    parser.add_argument("--mt5-self-test", action="store_true", help="Run safe MT5 detection diagnostics")
    parser.add_argument("--backtest-smoke-self-test", action="store_true", help="Write one safe smoke backtest result")
    parser.add_argument("--candidate-generator-self-test", action="store_true", help="Generate safe candidate JSON artifacts")
    parser.add_argument("--tournament-smoke-self-test", action="store_true", help="Run the safe MVP-006 tournament smoke")
    parser.add_argument("--risk-profile-self-test", action="store_true", help="Rank tournament candidates by risk profile")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        print(json.dumps(run_self_test(), indent=2, sort_keys=True))
        return 0
    if args.mt5_self_test:
        result = generate_diagnostics(PROJECT_ROOT / "reports" / "public")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.backtest_smoke_self_test:
        result = run_xauusd_base_seed_smoke(PROJECT_ROOT / "reports" / "public", allow_real_execution=False)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.candidate_generator_self_test:
        candidates = generate_candidates(DEFAULT_SEED)
        result = save_candidates(candidates, PROJECT_ROOT / "candidates")
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
        result = run_tournament(PROJECT_ROOT)
        print(json.dumps(result.__dict__, indent=2, sort_keys=True))
        return 0
    if args.risk_profile_self_test:
        run_tournament(PROJECT_ROOT)
        result = generate_risk_profile_report(
            PROJECT_ROOT / "reports" / "public" / "tournament_ranking.json",
            PROJECT_ROOT / "reports" / "public" / "risk_profile_ranking.json",
        )
        print(json.dumps(result.__dict__, indent=2, sort_keys=True))
        return 0
    launch_app(PROJECT_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
