import tempfile
import unittest
from pathlib import Path

from app.core.candidate_generator import (
    ALLOWED_PARAMETERS,
    DEFAULT_SEED,
    apply_constraints,
    generate_candidates,
    list_candidates,
    mutate_parameters,
    save_candidates,
)


class CandidateGeneratorTests(unittest.TestCase):
    def test_mutate_parameters_returns_bounded_mutations(self) -> None:
        mutations = mutate_parameters(DEFAULT_SEED)
        self.assertEqual(len(mutations), 5)
        for mutation in mutations:
            self.assertIn("mutation_origin", mutation)
            self.assertEqual(set(mutation["parameters"].keys()), set(ALLOWED_PARAMETERS))

    def test_generate_candidates_preserves_seed_trace(self) -> None:
        candidates = generate_candidates(DEFAULT_SEED)
        self.assertEqual(len(candidates), 5)
        ids = {candidate["candidate_id"] for candidate in candidates}
        self.assertEqual(len(ids), len(candidates))
        for candidate in candidates:
            self.assertEqual(candidate["seed_id"], DEFAULT_SEED["seed_id"])
            self.assertEqual(candidate["seed_trace"]["source_seed_id"], DEFAULT_SEED["seed_id"])
            self.assertFalse(candidate["mt5_real_run"])
            self.assertFalse(candidate["backtest_run"])
            self.assertTrue(candidate["constraints_applied"])

    def test_constraints_record_risk_without_blocking(self) -> None:
        candidate = {
            "parameters": {
                **DEFAULT_SEED["parameters"],
                "use_grid": True,
                "use_martingale": True,
                "SL": 0,
                "risk_percent": 10,
            }
        }
        constrained = apply_constraints(candidate)
        self.assertIn("grid_enabled", constrained["risk_flags"])
        self.assertIn("martingale_enabled", constrained["risk_flags"])
        self.assertIn("no_stop", constrained["risk_flags"])
        self.assertIn("high_risk_percent", constrained["risk_flags"])

    def test_save_and_list_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "candidates"
            result = save_candidates(generate_candidates(DEFAULT_SEED), root)
            loaded = list_candidates(root)
            log_path = Path(result.log_path)
            self.assertEqual(len(result.files), 5)
            self.assertEqual(len(loaded), 5)
            self.assertTrue(log_path.exists())
            self.assertTrue(log_path.name.endswith("candidate_generation_log.json"))


if __name__ == "__main__":
    unittest.main()
