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
from app.core.champion_dna import ChampionDNA, sample_champion_dna, write_champion_artifacts
from app.core.export_reports import export_sample_summary
from app.core.intelligence_modes import validate_intelligence_modes
from app.core.lab_registry import load_lab_registry
from app.core.symbol_mapping import TIMEFRAME_MINUTES
from app.ui.main_window import launch_app


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_self_test() -> dict[str, object]:
    config = load_app_config(PROJECT_ROOT / "config" / "app.default.json")
    validate_app_config(config)
    validate_intelligence_modes(config.supported_intelligence_modes, config.default_intelligence_mode)
    if config.default_timeframe not in TIMEFRAME_MINUTES:
        raise AssertionError("Default timeframe is not supported")

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
        "labs_loaded": [lab.id for lab in labs],
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
