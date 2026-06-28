import json
import tempfile
import unittest
from pathlib import Path

from app.core.risk_profile_ranking import generate_risk_profile_report, rank_by_risk_profile, select_profile_champions
from app.core.tournament_engine import run_tournament


class RiskProfileRankingTests(unittest.TestCase):
    def test_rank_by_risk_profile_filters_controlled_risk(self) -> None:
        candidates = [
            {
                "candidate_id": "plain",
                "seed_id": "seed",
                "mutation_origin": "plain",
                "profit": 10,
                "drawdown": 5,
                "trades": 1,
                "risk_flags": [],
            },
            {
                "candidate_id": "grid",
                "seed_id": "seed",
                "mutation_origin": "grid",
                "profit": 100,
                "drawdown": 5,
                "trades": 1,
                "risk_flags": ["grid_enabled"],
            },
        ]
        rankings = rank_by_risk_profile(candidates)
        controlled = rankings["controlled_risk"]
        wild = rankings["wild"]
        self.assertTrue(controlled[0]["profile_allowed"])
        self.assertEqual(controlled[0]["candidate_id"], "plain")
        self.assertFalse(next(row for row in controlled if row["candidate_id"] == "grid")["profile_allowed"])
        self.assertEqual(wild[0]["candidate_id"], "grid")

    def test_profile_champions_select_allowed_rows(self) -> None:
        rankings = rank_by_risk_profile(
            [
                {
                    "candidate_id": "martingale",
                    "seed_id": "seed",
                    "mutation_origin": "martingale",
                    "profit": 20,
                    "drawdown": 5,
                    "trades": 1,
                    "risk_flags": ["martingale_enabled"],
                },
                {
                    "candidate_id": "controlled",
                    "seed_id": "seed",
                    "mutation_origin": "controlled",
                    "profit": 1,
                    "drawdown": 5,
                    "trades": 1,
                    "risk_flags": [],
                },
            ]
        )
        champions = select_profile_champions(rankings)
        self.assertEqual(champions["controlled_risk"]["candidate_id"], "controlled")
        self.assertEqual(champions["wild"]["candidate_id"], "martingale")

    def test_generate_report_from_tournament_ranking(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            run_tournament(root)
            output = root / "reports" / "public" / "risk_profile_ranking.json"
            result = generate_risk_profile_report(root / "reports" / "public" / "tournament_ranking.json", output)
            self.assertTrue(output.exists())
            payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(result.status, "risk_profile_ranking_completed")
        self.assertIn("controlled_risk", payload["profiles"])
        self.assertIn("wild", payload["profiles"])
        self.assertFalse(payload["mt5_real_run"])
        self.assertFalse(payload["backtest_real_run"])


if __name__ == "__main__":
    unittest.main()
