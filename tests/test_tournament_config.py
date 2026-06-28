import tempfile
import unittest
from pathlib import Path

from app.core.tournament_config import (
    TournamentConfig,
    default_tournament_config,
    from_dict,
    make_public_summary,
    save_local_config,
    load_local_config,
    timeframe_to_minutes,
    to_dict,
    validate_tournament_config,
)


class TournamentConfigTests(unittest.TestCase):
    def test_default_config(self) -> None:
        config = default_tournament_config()
        self.assertEqual(config.lab_id, "ea-xau")
        self.assertEqual(config.lab_name, "XAU Robot Lab")
        self.assertEqual(config.requested_symbol, "XAUUSD")
        self.assertEqual(config.timeframe, "M5")
        self.assertEqual(config.timeframe_minutes, 5)
        self.assertEqual(config.initial_balance_usd, 10000)
        self.assertEqual(config.max_backtests, 100)
        self.assertEqual(config.champion_count, 10)
        self.assertEqual(config.intelligence_mode, "local_auto")
        self.assertFalse(config.codex_enabled)
        self.assertFalse(config.codex_authorized)

    def test_validation_success(self) -> None:
        validate_tournament_config(default_tournament_config())

    def test_invalid_timeframe(self) -> None:
        data = to_dict(default_tournament_config())
        data["timeframe"] = "M2"
        data["timeframe_minutes"] = 2
        with self.assertRaises(ValueError):
            validate_tournament_config(TournamentConfig(**data))

    def test_invalid_balance(self) -> None:
        data = to_dict(default_tournament_config())
        data["initial_balance_usd"] = 0
        with self.assertRaises(ValueError):
            validate_tournament_config(TournamentConfig(**data))

    def test_champion_count_lte_max_backtests(self) -> None:
        data = to_dict(default_tournament_config())
        data["champion_count"] = 101
        with self.assertRaises(ValueError):
            validate_tournament_config(TournamentConfig(**data))

    def test_timeframe_to_minutes(self) -> None:
        self.assertEqual(timeframe_to_minutes("M1"), 1)
        self.assertEqual(timeframe_to_minutes("M5"), 5)
        self.assertEqual(timeframe_to_minutes("H1"), 60)
        self.assertEqual(timeframe_to_minutes("D1"), 1440)

    def test_to_dict_from_dict(self) -> None:
        config = default_tournament_config()
        restored = from_dict(to_dict(config))
        self.assertEqual(restored.requested_symbol, config.requested_symbol)
        self.assertEqual(restored.timeframe, config.timeframe)
        self.assertEqual(restored.output_formats, config.output_formats)

    def test_save_load_temp(self) -> None:
        config = default_tournament_config()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "local.tournament.json"
            save_local_config(config, path)
            loaded = load_local_config(path)
        self.assertEqual(loaded.requested_symbol, "XAUUSD")
        self.assertEqual(loaded.timeframe, "M5")
        self.assertEqual(loaded.max_backtests, 100)

    def test_public_summary_safe(self) -> None:
        summary = make_public_summary(default_tournament_config())
        text = str(summary)
        self.assertNotIn("password", text.lower())
        self.assertNotIn("token", text.lower())
        self.assertNotIn("account", text.lower())
        self.assertNotIn("server", text.lower())
        self.assertNotIn("E:\\", text)

    def test_codex_assisted_allowed_but_not_required(self) -> None:
        data = to_dict(default_tournament_config())
        data["intelligence_mode"] = "codex_assisted"
        data["codex_enabled"] = True
        data["codex_authorized"] = False
        config = TournamentConfig(**data)
        validate_tournament_config(config)
        self.assertTrue(config.codex_enabled)
        self.assertFalse(config.codex_authorized)


if __name__ == "__main__":
    unittest.main()
