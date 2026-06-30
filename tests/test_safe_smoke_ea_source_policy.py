import re
import unittest
from pathlib import Path


SOURCE_PATH = Path("MQL5") / "Experts" / "MT5RobotLab" / "SmokeHarness_Public.mq5"


class SafeSmokeEASourcePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_text = SOURCE_PATH.read_text(encoding="utf-8")
        cls.lower_source = cls.source_text.lower()

    def test_safe_smoke_source_exists_in_public_repo(self) -> None:
        self.assertTrue(SOURCE_PATH.exists())
        self.assertIn("OnInit", self.source_text)
        self.assertIn("OnTick", self.source_text)
        self.assertIn("OnDeinit", self.source_text)
        self.assertIn("OnTester", self.source_text)

    def test_safe_smoke_source_contains_no_trade_operations(self) -> None:
        forbidden_terms = [
            "OrderSend",
            "CTrade",
            "PositionOpen",
            "PositionClose",
            "trade.Buy",
            "trade.Sell",
            ".Buy(",
            ".Sell(",
            "Buy(",
            "Sell(",
        ]
        for term in forbidden_terms:
            self.assertNotIn(term, self.source_text)

    def test_safe_smoke_source_contains_no_grid_or_martingale_logic(self) -> None:
        for term in ("martingale", "grid", "lot_multiplier", "averaging"):
            self.assertNotIn(term, self.lower_source)

    def test_safe_smoke_source_has_no_live_credentials_or_paths(self) -> None:
        self.assertNotRegex(self.source_text, re.compile(r"(?i)password|token|secret|account|server"))
        self.assertNotRegex(self.source_text, re.compile(r"(?i)[a-z]:[\\/]"))


if __name__ == "__main__":
    unittest.main()
