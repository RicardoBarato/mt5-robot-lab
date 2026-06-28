import unittest

from app.core.leaderboard_schema import (
    build_leaderboard_entry,
    category_key,
    default_leaderboard_categories,
    make_public_leaderboard_sample,
    rank_entries,
    validate_leaderboard_entry,
)


class LeaderboardSchemaTests(unittest.TestCase):
    def sample_manifest(self, **overrides):
        manifest = {
            "submission_id": "submission_test",
            "champion_id": "champion_test",
            "candidate_id": "candidate_test",
            "app_version": "mvp-010",
            "package_version": "1.0",
            "requested_symbol": "XAUUSD",
            "broker_symbol": "XAUUSD",
            "timeframe": "M5",
            "timeframe_minutes": 5,
            "backtest_years": 2.0,
            "initial_balance_usd": 10000.0,
            "risk_profile": "wild",
            "risk_mode": "wild",
            "max_drawdown_tolerated_pct": 100.0,
            "net_profit_usd": 100.0,
            "max_drawdown_pct": 10.0,
            "profit_factor": 1.2,
            "total_trades": 10,
            "win_rate": 40.0,
            "mt5_real_run": False,
            "backtest_real_run": False,
            "validation_status": "sample_not_real_backtest",
            "upload_ready": False,
            "user_display_name": "sample_user",
            "team_name": "sample_team",
            "country": "BR",
        }
        manifest.update(overrides)
        return manifest

    def test_default_categories_exist(self) -> None:
        categories = default_leaderboard_categories()
        self.assertIn("XAUUSD", categories["asset_symbol"])
        self.assertIn("M5", categories["timeframe"])
        self.assertIn("highest_net_profit", categories["ranking_mode"])

    def test_build_and_validate_entry(self) -> None:
        entry = build_leaderboard_entry(self.sample_manifest())
        validate_leaderboard_entry(entry)
        self.assertEqual(entry["user_display_name"], "sample_user")
        self.assertEqual(entry["country"], "BR")
        self.assertFalse(entry["mt5_real_run"])
        self.assertFalse(entry["backtest_real_run"])
        self.assertFalse(entry["upload_ready"])

    def test_category_key(self) -> None:
        entry = build_leaderboard_entry(self.sample_manifest())
        key = category_key(entry)
        self.assertIn("XAUUSD", key)
        self.assertIn("M5", key)
        self.assertIn("wild", key)

    def test_rank_entries_highest_net_profit(self) -> None:
        low = build_leaderboard_entry(self.sample_manifest(submission_id="low", net_profit_usd=50))
        high = build_leaderboard_entry(self.sample_manifest(submission_id="high", net_profit_usd=200))
        ranked = rank_entries([low, high], "highest_net_profit")
        self.assertEqual(ranked[0]["submission_id"], "high")
        self.assertEqual(ranked[0]["leaderboard_rank"], 1)

    def test_rank_entries_lowest_drawdown(self) -> None:
        high_dd = build_leaderboard_entry(self.sample_manifest(submission_id="high_dd", max_drawdown_pct=20))
        low_dd = build_leaderboard_entry(self.sample_manifest(submission_id="low_dd", max_drawdown_pct=5))
        ranked = rank_entries([high_dd, low_dd], "lowest_drawdown")
        self.assertEqual(ranked[0]["submission_id"], "low_dd")

    def test_public_sample_is_not_real_or_upload_ready(self) -> None:
        sample = make_public_leaderboard_sample()
        entry = sample["entries"][0]
        validate_leaderboard_entry(entry)
        self.assertEqual(sample["status"], "sample_not_real_backtest")
        self.assertFalse(sample["mt5_real_run"])
        self.assertFalse(sample["backtest_real_run"])
        self.assertFalse(sample["upload_ready"])
        self.assertEqual(entry["validation_status"], "sample_not_real_backtest")
        text = str(sample).lower()
        for forbidden in ["password", "senha", "token", "secret", "api_key"]:
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
