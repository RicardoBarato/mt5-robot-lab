import unittest

from app.core.symbol_mapping import candidates_for_asset, suggest_symbol, timeframe_minutes


class SymbolMappingTests(unittest.TestCase):
    def test_gold_candidates_include_common_names(self) -> None:
        self.assertIn("XAUUSD", candidates_for_asset("gold_xau"))
        self.assertIn("GOLD", candidates_for_asset("gold_xau"))

    def test_suggest_symbol_prefers_available(self) -> None:
        self.assertEqual(suggest_symbol("XAUUSD", ["GOLD"]), "GOLD")

    def test_timeframe_minutes(self) -> None:
        self.assertEqual(timeframe_minutes("M5"), 5)
        self.assertEqual(timeframe_minutes("H1"), 60)


if __name__ == "__main__":
    unittest.main()
