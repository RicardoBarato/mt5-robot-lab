import json
import tempfile
import unittest
from pathlib import Path

from app.core.tournament_engine import (
    collect_results,
    execute_candidates,
    load_candidates,
    rank_candidates,
    run_tournament,
    select_champion,
)


class TournamentEngineTests(unittest.TestCase):
    def test_load_candidates_generates_default_smoke_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            candidates = load_candidates(Path(tmpdir) / "candidates")
        self.assertEqual(len(candidates), 5)

    def test_execute_candidates_runs_one_smoke_per_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            candidates = load_candidates(Path(tmpdir) / "candidates")
            executions = execute_candidates(candidates)
        self.assertEqual(len(executions), 5)
        for execution in executions:
            self.assertEqual(execution["backtests_executed"], 1)
            self.assertEqual(execution["execution_mode"], "smoke_only")
            self.assertFalse(execution["result"]["mt5_real_execution"])
            self.assertFalse(execution["result"]["strategy_tester_executed"])

    def test_ranking_and_champion_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            candidates = load_candidates(Path(tmpdir) / "candidates")
            collected = collect_results(execute_candidates(candidates))
            ranking = rank_candidates(collected)
            champion = select_champion(ranking)
        self.assertEqual(len(ranking), 5)
        self.assertIsNotNone(champion)
        self.assertEqual(champion["rank"], 1)
        self.assertEqual(champion["ranking_metric"], "profit")

    def test_run_tournament_writes_public_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = run_tournament(root)
            reports = result.reports
            for path in reports.values():
                self.assertTrue(Path(path).exists())
            payload = json.loads(Path(reports["result"]).read_text(encoding="utf-8"))
            ranking = json.loads(Path(reports["ranking"]).read_text(encoding="utf-8"))
        self.assertEqual(result.status, "tournament_smoke_completed")
        self.assertEqual(result.candidates_loaded, 5)
        self.assertTrue(result.execution_done)
        self.assertTrue(result.ranking_generated)
        self.assertTrue(result.champion_selected)
        self.assertFalse(result.mt5_real_run)
        self.assertFalse(result.backtest_real_run)
        self.assertFalse(result.loop_execution)
        self.assertEqual(payload["status"], "tournament_smoke_completed")
        self.assertEqual(len(ranking), 5)


if __name__ == "__main__":
    unittest.main()
