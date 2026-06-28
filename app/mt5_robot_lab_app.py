#!/usr/bin/env python3
"""MT5 Robot Lab desktop bootstrap."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

if __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.app_config import load_app_config, validate_app_config
from app.core.champion_dna import ChampionDNA, sample_champion_dna, write_champion_artifacts
from app.core.export_reports import export_sample_summary
from app.core.intelligence_modes import validate_intelligence_modes
from app.core.lab_registry import load_lab_registry
from app.core.symbol_mapping import TIMEFRAME_MINUTES
from app.core.tournament_config import (
    default_tournament_config,
    load_local_config,
    make_public_summary,
    save_local_config,
    timeframe_to_minutes,
    validate_tournament_config,
    write_public_preview,
)
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

    tournament = default_tournament_config()
    validate_tournament_config(tournament)
    if tournament.champion_count > tournament.max_backtests:
        raise AssertionError("champion_count must be <= max_backtests")
    if timeframe_to_minutes("M5") != 5:
        raise AssertionError("M5 timeframe must equal 5 minutes")
    if tournament.intelligence_mode != "local_auto":
        raise AssertionError("Default intelligence mode must be local_auto")
    if set(tournament.output_formats) - {"csv", "md", "xlsx"}:
        raise AssertionError("Unsupported output format in default tournament config")
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir) / "local.tournament.json"
        save_local_config(tournament, temp_path)
        loaded = load_local_config(temp_path)
        if loaded.requested_symbol != tournament.requested_symbol or loaded.timeframe != tournament.timeframe:
            raise AssertionError("Tournament config load is not stable")
    public_summary = make_public_summary(tournament)
    summary_text = json.dumps(public_summary, sort_keys=True)
    forbidden_public_fragments = ["password", "token", "account", "server", "E:\\"]
    if any(fragment in summary_text for fragment in forbidden_public_fragments):
        raise AssertionError("Public tournament summary contains a forbidden fragment")

    labs = load_lab_registry(PROJECT_ROOT / "config" / "labs.example.json")
    if not labs:
        raise AssertionError("At least one lab example is required")

    dna = sample_champion_dna()
    if not isinstance(dna, ChampionDNA):
        raise AssertionError("Champion DNA sample did not build")

    artifact_root = PROJECT_ROOT / "reports" / "public" / "sample_champion_dna"
    written = write_champion_artifacts(dna, artifact_root)
    exports = export_sample_summary(PROJECT_ROOT / "reports" / "public")
    tournament_preview = write_public_preview(tournament, PROJECT_ROOT / "reports" / "public")

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
        "tournament_config": public_summary,
        "tournament_preview": {key: str(value) for key, value in tournament_preview.items()},
        "champion_artifacts": {key: str(value) for key, value in written.items()},
        "exports": {key: str(value) for key, value in exports.items()},
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MT5 Robot Lab")
    parser.add_argument("--self-test", action="store_true", help="Run non-GUI validation")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        print(json.dumps(run_self_test(), indent=2, sort_keys=True))
        return 0
    launch_app(PROJECT_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
