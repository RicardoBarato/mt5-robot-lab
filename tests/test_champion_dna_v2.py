import tempfile
import unittest
from pathlib import Path

from app.core.candidate_generator import DEFAULT_SEED
from app.core.champion_dna import (
    create_champion_dna,
    hash_source_text,
    load_champion_dna,
    make_public_champion_summary,
    parameter_diff,
    sample_champion_dna,
    save_champion_dna,
    summarize_adjustments,
    validate_champion_dna,
)
from app.core.tournament_engine import run_tournament


class ChampionDNAV2Tests(unittest.TestCase):
    def _candidate(self) -> dict:
        return {
            "candidate_id": "candidate_001",
            "seed_id": DEFAULT_SEED["seed_id"],
            "rank": 1,
            "parameters": {
                **DEFAULT_SEED["parameters"],
                "ATR_period": 21,
                "ADX_min": 18,
                "TP_R": 3.5,
                "SL": 0,
                "use_grid": True,
                "use_martingale": True,
            },
            "risk_flags": ["grid_enabled", "martingale_enabled", "no_stop"],
        }

    def _metrics(self) -> dict:
        return {
            "net_profit_usd": 0,
            "final_balance_usd": 10000,
            "max_drawdown_usd": 0,
            "max_drawdown_pct": 0,
            "profit_factor": 0,
            "expected_payoff": 0,
            "total_trades": 0,
            "win_rate": 0,
            "largest_loss_streak": 0,
        }

    def test_create_and_validate_wild_dna(self) -> None:
        dna = create_champion_dna(
            self._candidate(),
            self._metrics(),
            {"initial_balance_usd": 10000, "timeframe": "M5"},
            {"profile_id": "wild", "max_drawdown_tolerated": 100.0, "profile_allowed": True},
        )
        validate_champion_dna(dna)
        self.assertEqual(dna.risk_mode, "wild")
        self.assertEqual(dna.max_drawdown_tolerated_pct, 100.0)
        self.assertTrue(dna.grid_used)
        self.assertTrue(dna.martingale_used)
        self.assertTrue(dna.no_stop_used)

    def test_controlled_mode_registers_20_percent_dd(self) -> None:
        dna = create_champion_dna(
            self._candidate(),
            self._metrics(),
            {},
            {
                "profile_id": "controlled_risk",
                "max_drawdown_tolerated": 20.0,
                "profile_allowed": False,
                "profile_rejection_reasons": ["grid_not_allowed_in_profile"],
            },
        )
        validate_champion_dna(dna)
        self.assertEqual(dna.risk_mode, "controlled_risk")
        self.assertEqual(dna.max_drawdown_tolerated_pct, 20.0)
        self.assertIn("Controlled Risk", dna.ranking_reason)

    def test_parameter_diff_and_summary(self) -> None:
        diff = parameter_diff({"ATR_period": 14, "use_grid": False}, {"ATR_period": 21, "use_grid": True})
        names = {item["parameter"] for item in diff}
        self.assertEqual(names, {"ATR_period", "use_grid"})
        self.assertIn("risk_increase", {item["risk_impact"] for item in diff})
        dna = sample_champion_dna()
        summary = summarize_adjustments(dna)
        public = make_public_champion_summary(dna)
        self.assertIn("ATR_period", summary)
        self.assertIn("Champion DNA v2", public)
        lowered = public.lower()
        for forbidden in ["password", "senha", "token", "secret", "api_key", "c:\\"]:
            self.assertNotIn(forbidden, lowered)

    def test_save_load_and_hash_are_deterministic(self) -> None:
        self.assertEqual(hash_source_text("abc"), hash_source_text("abc"))
        self.assertNotEqual(hash_source_text("abc"), hash_source_text("abcd"))
        dna = sample_champion_dna()
        with tempfile.TemporaryDirectory() as tmpdir:
            written = save_champion_dna(dna, Path(tmpdir))
            loaded = load_champion_dna(written["champion_dna_v2"])
        self.assertEqual(loaded.champion_id, dna.champion_id)

    def test_tournament_engine_generates_champion_dna_v2(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_tournament(Path(tmpdir))
            dna_path = Path(result.reports["champion_dna_v2"])
            summary_path = Path(result.reports["champion_public_summary_v2"])
            self.assertTrue(dna_path.exists())
            self.assertTrue(summary_path.exists())
            dna = load_champion_dna(dna_path)
        self.assertEqual(dna.status, "smoke_or_dry_run")
        self.assertFalse(dna.mt5_real_run)
        self.assertFalse(dna.backtest_real_run)


if __name__ == "__main__":
    unittest.main()
